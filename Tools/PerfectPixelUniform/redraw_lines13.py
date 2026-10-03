"""Source-connected finite strokes. No endpoint completion or inferred corners."""
import numpy as np
from PIL import Image, ImageDraw
from redraw_geometry13 import cv2


def thin(mask):
    """Zhang--Suen parallel thinning: remove pixels, never add or join them."""
    m = np.pad(np.asarray(mask, np.uint8), 1)
    while True:
        changed = False
        for phase in (0, 1):
            p = [m[:-2,1:-1], m[:-2,2:], m[1:-1,2:], m[2:,2:],
                 m[2:,1:-1], m[2:,:-2], m[1:-1,:-2], m[:-2,:-2]]
            count = sum(p)
            transitions = sum((p[i] == 0) & (p[(i+1)%8] != 0) for i in range(8))
            if phase == 0:
                guard = (p[0]*p[2]*p[4] == 0) & (p[2]*p[4]*p[6] == 0)
            else:
                guard = (p[0]*p[2]*p[6] == 0) & (p[0]*p[4]*p[6] == 0)
            remove = (m[1:-1,1:-1] != 0) & (count >= 2) & (count <= 6) & (transitions == 1) & guard
            if np.any(remove):
                m[1:-1,1:-1][remove] = 0
                changed = True
        if not changed:
            return m[1:-1,1:-1].astype(bool)


def chains(mask):
    """Trace existing graph edges once; cycles close only if already present."""
    vertices = {tuple(v) for v in np.argwhere(mask)}
    adjacent = {}
    for y, x in sorted(vertices):
        neighbors = []
        for dy in (-1,0,1):
            for dx in (-1,0,1):
                q = (y+dy,x+dx)
                if (not dy and not dx) or q not in vertices:
                    continue
                # Do not make tiny triangular branches around a staircase turn.
                if dy and dx and ((y+dy,x) in vertices or (y,x+dx) in vertices):
                    continue
                neighbors.append(q)
        adjacent[(y,x)] = sorted(neighbors)
    seen = set(); paths = []
    def walk(a,b):
        path = [a,b]; seen.add(tuple(sorted((a,b))))
        while len(adjacent[b]) == 2:
            following = next(v for v in adjacent[b] if v != a)
            key = tuple(sorted((b,following)))
            if key in seen:
                break
            seen.add(key); path.append(following); a,b = b,following
        paths.append(np.array(path)[:,::-1].astype(float)+.5)
    for a in sorted(vertices, key=lambda v:(len(adjacent[v]) == 2,v)):
        for b in adjacent[a]:
            if tuple(sorted((a,b))) not in seen:
                walk(a,b)
    return paths


def source_strokes(mask, minimum_length=12., narrow_only=False):
    """Bounded polyline approximation of actual finite source chains."""
    skeleton = thin(mask)
    # Minimum support belongs to a connected component, not each branch.
    # Dropping a short corner branch of a long frame breaks that real frame.
    count,labels,stats,_=cv2.connectedComponentsWithStats(skeleton.astype(np.uint8),8)
    keep=[i for i in range(1,count) if stats[i,cv2.CC_STAT_AREA]>=minimum_length]
    skeleton &= np.isin(labels,keep)
    radius = cv2.distanceTransform(np.asarray(mask,np.uint8),cv2.DIST_L2,5)
    paths = []
    for chain in chains(skeleton):
        length = np.linalg.norm(np.diff(chain,axis=0),axis=1).sum()
        xy = np.floor(chain).astype(int)
        width = float(2*np.median(radius[xy[:,1],xy[:,0]]))
        if narrow_only and width >= 5.2:
            continue
        closed = bool(np.array_equal(chain[0],chain[-1]))
        points = cv2.approxPolyDP(chain.astype(np.float32),1.25,closed).reshape(-1,2)
        if closed and not np.array_equal(points[0],points[-1]):
            points = np.vstack((points,points[0]))
        paths.append({'points':points.tolist(),'source_length':float(length),
                      'width':width,'closed':closed})
    return paths,skeleton


def raster_strokes(paths,g,allowed):
    """One source graph, one owned stroke union; retain only supported cells."""
    canvas = Image.new('I',tuple(g['size']),0); draw = ImageDraw.Draw(canvas)
    origin = np.array(g['origin'])
    for index,path in enumerate(paths,1):
        points = np.floor((np.array(path['points'])-origin)/g['pitch']).astype(int)
        draw.line([tuple(v) for v in points],fill=index,width=1)
    owners=np.array(canvas);raw=owners>0
    # A common junction can make a 2x2 block after snapping. Remove only pixels
    # from this union. This does not extend endpoints or fill a missing region.
    supported = raw & allowed
    final=thin(supported);owners[~final]=0
    return final, {'submitted_cells':int(raw.sum()),
                   'unsupported_cells_rejected':int((raw&~allowed).sum())},owners
