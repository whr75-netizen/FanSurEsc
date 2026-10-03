"""Read saved V6 production artifacts and check their explicit technical contract.

This does not rerender, repair, grade artwork or claim reference reconstruction.
The validation report is a new immutable artifact, including failures.
"""
from __future__ import annotations

import argparse
from collections import deque
import hashlib
import json
import math
from pathlib import Path
import re
import sys
import time

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
COMMON = ROOT / "Tools/PixelPipeline/common.py"
sys.path.insert(0,str(COMMON.parent))
from common import basis, consistent_edges, parallel_double_strokes


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path,value):
    text=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+"\n"
    with Path(path).open("w",encoding="utf-8",newline="\n") as stream:
        stream.write(text)


def connected_sizes(mask):
    """Independent eight-connected binary component enumeration."""
    visited=np.zeros_like(mask,bool); height,width=mask.shape; sizes=[]
    for yy,xx in np.argwhere(mask):
        yy,xx=int(yy),int(xx)
        if visited[yy,xx]: continue
        visited[yy,xx]=True; queue=deque([(yy,xx)]); total=0
        while queue:
            y,x=queue.popleft(); total+=1
            for dy in (-1,0,1):
                for dx in (-1,0,1):
                    qy,qx=y+dy,x+dx
                    if 0<=qy<height and 0<=qx<width and mask[qy,qx] and not visited[qy,qx]:
                        visited[qy,qx]=True; queue.append((qy,qx))
        sizes.append(total)
    return sizes


class Audit:
    def __init__(self,output,recipe_path):
        self.output=output; self.recipe_path=recipe_path
        self.checks=[]; self.files={}; self.observations={}; self.started=time.perf_counter()

    def check(self,label,condition,observed=None):
        entry={"check":label,"passed":bool(condition)}
        if observed is not None: entry["observed"]=observed
        self.checks.append(entry)

    def file(self,path):
        path=Path(path)
        self.check("file_present:"+str(path.relative_to(self.output) if path.is_relative_to(self.output) else path),path.is_file())
        if not path.is_file(): raise FileNotFoundError(str(path))
        self.files[str(path.resolve())]=sha(path)
        return path

    def json(self,path):
        return read(self.file(path))

    def npz(self,path):
        with np.load(self.file(path),allow_pickle=False) as data:
            return {name:data[name].copy() for name in data.files}

    def image(self,path):
        with Image.open(self.file(path)) as image:
            self.check("rgba_source_mode:"+path.name,image.mode=="RGBA",image.mode)
            return np.array(image.convert("RGBA"),dtype=np.uint8)

    def declared_hashes(self,data,metadata_path):
        # The producer uses input_sha256/output_sha256 path -> digest maps.
        # Resolve absolute, output-relative and workspace-relative paths only.
        found=0
        for key in ("inputs","outputs","input_sha256","inputs_sha256","output_sha256","outputs_sha256"):
            mapping=data.get(key)
            if mapping is None: continue
            if not isinstance(mapping,dict):
                self.check("hash_map:"+metadata_path.name+":"+key,False); continue
            for raw,value in mapping.items():
                p=Path(raw)
                candidates=[p] if p.is_absolute() else [self.output/p,metadata_path.parent/p,ROOT/p]
                p=next((q for q in candidates if q.is_file()),candidates[0])
                valid=p.is_file() and isinstance(value,str) and sha(p)==value
                self.check("declared_sha:"+metadata_path.name+":"+str(raw),valid)
                if p.is_file(): self.files[str(p.resolve())]=sha(p)
                found+=1
        self.check("input_output_hash_maps:"+metadata_path.name,found>0,found)

    def material(self,recipe):
        source=ROOT/recipe["source"]
        self.file(source)
        self.check("recipe_source_sha",sha(source)==recipe["source_sha256"])
        with Image.open(source) as im: source_rgba=np.array(im.convert("RGBA"),np.uint8)
        palette=self.json(self.output/"material/palette.json")
        material=self.json(self.output/"material/material.json")
        self.check("palette_source_sha",palette.get("source_sha256")==sha(source))
        roles=("paint","wood","brass"); names=("light","base","shade","edge")
        colours=palette["colors_srgb8byrole"]
        rows=recipe["palette_sample_rows"]; columns=recipe["palette_sample_columns"]
        seen=set()
        for sample in palette["samples"]:
            role=sample["role"]; band=sample["band"]
            index=names.index(band) if isinstance(band,str) else int(band)
            x,y=[int(v) for v in sample["source_xy"]]
            inbounds=0<=x<source_rgba.shape[1] and 0<=y<source_rgba.shape[0]
            self.check(f"palette_coordinate:{role}:{index}",inbounds and [x,y]==[columns[role],rows[index]],[x,y])
            self.check(f"palette_raw_rgb:{role}:{index}",inbounds and source_rgba[y,x,3]==255
                       and source_rgba[y,x,:3].tolist()==sample["rgb"]==colours[role][index])
            seen.add((role,index))
        self.check("twelve_role_samples",seen=={(r,i) for r in roles for i in range(4)},len(seen))
        flat=np.array([c for role in roles for c in colours[role]],np.uint8)
        self.check("palette_shape",flat.shape==(12,3),list(flat.shape))
        grain=np.load(self.file(self.output/"material/grain.npy"),allow_pickle=False)
        self.check("material_grain_binary",grain.ndim==2 and (np.issubdtype(grain.dtype,np.integer) or grain.dtype==np.bool_)
                   and set(np.unique(grain).tolist())<={0,1},list(grain.shape))
        sizes=connected_sizes(grain==1)
        minimum=int(recipe["grain_minimum_component_pixels"])
        self.check("material_grain_no_small_islands",bool(sizes) and min(sizes)>=minimum,
                   {"components":len(sizes),"minimum_size":min(sizes) if sizes else None})
        self.observations["material"]={"palette_source":"exact centre pixels of generated source",
               "palette_unique_colours":int(len(np.unique(flat,axis=0))),
               "grain_size":[int(grain.shape[1]),int(grain.shape[0])],"minimum_dark_component":min(sizes) if sizes else None,
               "semantic_limit":"Generated reference is design input; its hidden dimensions are not uniquely recovered."}
        # Optional producer maps are checked if present; known artifacts remain
        # independently hashed in this report even without extra metadata maps.
        if any(k in material for k in ("inputs","outputs","input_sha256","output_sha256")):
            self.declared_hashes(material,self.output/"material/material.json")
        self.check("material_palette_sha",material.get("palette_sha256")==sha(self.output/"material/palette.json"))
        self.check("material_grain_sha",material.get("grain_sha256")==sha(self.output/"material/grain.npy"))
        self.material_info=material; self.grain_map=grain
        return flat,grain

    @staticmethod
    def nearest_box(origin,direction,boxes):
        hits=[]
        for box in boxes:
            low=np.array(box["minimum"],float); high=np.array(box["maximum"],float)
            near,far=-math.inf,math.inf
            for axis in range(3):
                if abs(direction[axis])<1e-12:
                    if origin[axis]<low[axis] or origin[axis]>high[axis]: near=math.inf; break
                else:
                    a,b=sorted(((low[axis]-origin[axis])/direction[axis],(high[axis]-origin[axis])/direction[axis]))
                    near,far=max(near,a),min(far,b)
            if far>=max(0.,near): hits.append((max(near,0.),int(box["part"])))
        return min(hits) if hits else None

    def variant(self,count,recipe,spec,flat):
        b=self.npz(self.output/f"geometry/buffers{count}.npz")
        raster=self.json(self.output/f"geometry/raster{count}.json")
        s=self.npz(self.output/f"pixels/shading{count}.npz")
        metadata_path=self.output/f"pixels/pixel{count}.json"
        pixel=self.json(metadata_path)
        self.declared_hashes(pixel,metadata_path)
        actual=self.image(self.output/f"pixels/native{count}.png")
        preview=self.image(self.output/f"pixels/preview{count}-x4.png")
        m=b["mask"]; height,width=m.shape
        self.check(f"n{count}:array_shapes",actual.shape==(height,width,4)
                   and all(b[k].shape==m.shape for k in ("part","face","depth","visibility"))
                   and all(b[k].shape==(height,width,3) for k in ("positions","normals")))
        self.check(f"n{count}:binary_alpha",set(np.unique(actual[...,3]).tolist())<={0,255})
        self.check(f"n{count}:alpha_geometry_match",np.array_equal(actual[...,3]==255,m))
        self.check(f"n{count}:finite_buffers",np.isfinite(b["positions"]).all()
                   and np.isfinite(b["normals"]).all() and np.isfinite(b["depth"]).all())
        self.check(f"n{count}:normal_unit",np.allclose(np.linalg.norm(b["normals"][m],axis=1),1,atol=1e-6))
        self.check(f"n{count}:finite_surface_ids",((b["part"][m]>=0)&(b["part"][m]<len(spec["groups"]))
                   &(b["face"][m]>=0)&(b["face"][m]<6)).all()
                   and (b["part"][~m]==-1).all() and (b["face"][~m]==-1).all())
        colours={tuple(c) for c in flat.tolist()}
        output_colours={tuple(c) for c in np.unique(actual[m,:3],axis=0).tolist()}
        self.check(f"n{count}:source_palette_only",output_colours<=colours,len(output_colours))
        indices=s["palette_index"]
        valid_indices=indices.shape==m.shape and np.issubdtype(indices.dtype,np.integer) and ((indices[m]>=0)&(indices[m]<4)).all()
        self.check(f"n{count}:palette_index_valid",valid_indices)
        if valid_indices:
            expected_rgb=np.zeros_like(actual[...,:3]); offsets={"paint":0,"wood":4,"brass":8}
            for group in spec["groups"]:
                region=b["part"]==group["id"]
                expected_rgb[region]=flat[offsets[group["role"]]+indices[region]]
            self.check(f"n{count}:final_rgb_matches_indices",np.array_equal(actual[m,:3],expected_rgb[m]))
        edge,_,policies=consistent_edges(b,raster["camera"])
        self.check(f"n{count}:visible_edge_owners",np.array_equal(s["ink"],edge))
        self.check(f"n{count}:ink_inside_geometry",not (s["ink"]&~m).any())
        double=parallel_double_strokes(b,s["ink"])
        self.check(f"n{count}:parallel_double_strokes_absent",not double,double)
        self.check(f"n{count}:exact_fourfold_preview",np.array_equal(preview,np.repeat(np.repeat(actual,4,axis=0),4,axis=1)))
        self.check(f"n{count}:geometry_no_source_rgb",raster.get("source_rgb_used") is False and raster.get("image_resize") is False)
        self.check(f"n{count}:native_centres",raster.get("native_pixel_centres") is True)
        expected_density=64*math.sqrt(2)
        self.check(f"n{count}:fixed_density",abs(float(raster["pixels_per_meter"])-expected_density)<1e-10)
        self.check(f"n{count}:whole_origin_phase",np.allclose(raster["screen_origin"],np.rint(raster["screen_origin"]),atol=1e-10))
        self.check(f"n{count}:projection_formula",float(raster["projection_max_error_px"])<=1e-10)
        self.check(f"n{count}:actual_shadow",int((m&~b["visibility"]).sum())>0,
                   int((m&~b["visibility"]).sum()))
        observed_visible={g["name"]:int((b["part"]==g["id"]).sum()) for g in spec["groups"]}
        required=[f"Bay{i}{suffix}" for i in range(count) for suffix in
                  ("DoorFrame","DoorInset","DrawerFrame","DrawerInset","DoorHandle","DrawerHandle")]+["SideFrame","SideInset"]
        self.check(f"n{count}:required_detail_groups_visible",all(observed_visible.get(name,0)>0 for name in required),
                   {name:observed_visible.get(name,0) for name in required})
        self.check(f"n{count}:raster_buffer_sha",raster.get("buffers_sha256")==sha(self.output/f"geometry/buffers{count}.npz"))
        r,u,d=basis(raster["camera"]); origin_px=np.array(raster["screen_origin"]); camera_distance=float(raster["camera_distance"])
        independent=[]
        for group in spec["groups"]:
            samples=np.argwhere(b["part"]==group["id"])
            if not len(samples): continue
            y,x=[int(v) for v in samples[len(samples)//2]]
            q=(origin_px+np.array([x+.5,y+.5]))/expected_density
            origin=r*q[0]-u*q[1]+d*camera_distance
            hit=self.nearest_box(origin,-d,spec["boxes"])
            error=abs(float(hit[0])-float(b["depth"][y,x])) if hit else None
            correct=hit is not None and hit[1]==int(b["part"][y,x]) and error<1e-5
            self.check(f"n{count}:independent_depth:{group['name']}",correct,
                       {"pixel":[x,y],"depth_error_m":error})
            independent.append({"group":group["name"],"passed":correct})
        # Band and grain maps must stay separate from ink and source RGB.
        self.check(f"n{count}:separate_band_grain_maps",s["band"].shape==m.shape and s["grain"].shape==m.shape
                   and np.isfinite(s["band"]).all() and np.isfinite(s["grain"]).all())
        light=np.array(recipe["lighting"]["to_light"],float); light/=np.linalg.norm(light)
        self.check(f"n{count}:recipe_light_direction",np.allclose(raster["to_light_world"],light,atol=1e-12))
        diffuse=b["normals"]@light
        low,high=recipe["lighting"]["band_thresholds"]
        expected_band=np.where(diffuse>=high,0,np.where(diffuse>=low,1,2)).astype(np.uint8)
        expected_band[m&~b["visibility"]]=2
        self.check(f"n{count}:normal_visibility_band_selection",np.array_equal(s["band"][m],expected_band[m]))
        pos=b["positions"]
        lx,ly,lz=pos[...,1]*32,pos[...,2]*32*math.sqrt(6),-pos[...,0]*32
        tu=np.where(np.abs(b["normals"][...,1])>.5,lz,lx)
        tv=np.where(np.abs(b["normals"][...,2])>.5,lz,ly)
        periods=self.material_info["tile_ticks"]; gh,gw=self.grain_map.shape
        uvx=np.clip(np.floor(np.mod(tu,periods[0])/periods[0]*gw).astype(int),0,gw-1)
        uvy=np.clip(np.floor(np.mod(tv,periods[1])/periods[1]*gh).astype(int),0,gh-1)
        wood=np.zeros_like(m)
        for group in spec["groups"]:
            if group["role"]=="wood": wood|=b["part"]==group["id"]
        expected_grain=wood&self.grain_map[uvy,uvx]
        self.check(f"n{count}:fixed_world_uv_grain",np.array_equal(s["grain"],expected_grain))
        expected_index=np.minimum(expected_band+expected_grain.astype(np.uint8),3)
        expected_index[edge]=3
        self.check(f"n{count}:separate_material_shading_fill",np.array_equal(indices[m],expected_index[m]))
        self.observations[f"variant{count}"]={"native_size":[width,height],"colours":len(output_colours),
                  "foreground_pixels":int(m.sum()),"visible_groups":observed_visible,
                  "independent_box_rays":len(independent),"boundary_policies":len(policies),
                  "shadow_pixels":int((m&~b["visibility"]).sum())}
        return raster

    def module_geometry(self,recipe,specs):
        profiles=[]
        for spec in specs:
            count=spec["count"]
            self.check(f"n{count}:module_width_formula",spec["width_ticks"]==2*recipe["cap"]+count*recipe["module_pitch"])
            self.check(f"n{count}:unchanged_height_depth",spec["height_ticks"]==recipe["height"] and spec["depth_ticks"]==recipe["depth"])
            groups={g["id"]:g for g in spec["groups"]}
            for box in spec["boxes"]:
                self.check("mesh_readback:"+box["name"],box.get("mesh_readback_bounds_match") is True)
                g=groups[box["part"]]
                if g["bay"] is None: continue
                offset=float(recipe["cap"]+g["bay"]*recipe["module_pitch"])
                low=np.array(box["local_minimum_ticks"],float); high=np.array(box["local_maximum_ticks"],float)
                low[0]-=offset; high[0]-=offset
                kind=re.sub(r"^Bay\d+","",g["name"])
                component=box["name"].split(g["name"]+"_",1)[1]
                profiles.append((kind,component,tuple(low.tolist()),tuple(high.tolist()),g["role"]))
        by_kind={}
        for kind,component,low,high,role in profiles:
            by_kind.setdefault((kind,component),set()).add((low,high,role))
        self.check("repeated_module_dimensions_identical",bool(by_kind) and all(len(v)==1 for v in by_kind.values()),
                   {kind+":"+component:len(values) for (kind,component),values in by_kind.items()})

    def run(self):
        recipe=self.json(self.recipe_path)
        provenance=self.json(ROOT/"Tools/PerfectPixelUniform/Source06/provenance.json")
        reference=ROOT/provenance["design_reference"]
        self.file(reference)
        self.check("v5_native_preserved",sha(reference)==provenance["reference_sha256"])
        for filename,key in (("geometry.npz","geometry_reference_sha256"),
                             ("geometry.json","geometry_metadata_reference_sha256")):
            path=reference.parent/filename; self.file(path)
            self.check("v5_"+filename+"_preserved",sha(path)==provenance[key])
        previous=self.json(reference.parent/"material.json")
        previous_code=ROOT/"Tools/PerfectPixelUniform/draw_parametric.py"
        self.file(previous_code)
        self.check("v5_code_preserved",sha(previous_code)==previous["code_sha256"])
        previous_recipe=self.json(ROOT/"Tools/PerfectPixelUniform/cabinet_recipe.json")
        previous_source=ROOT/previous_recipe["reference"]; self.file(previous_source)
        self.check("original_sheet_preserved",sha(previous_source)==previous_recipe["reference_sha256"])
        flat,_=self.material(recipe)
        parts=self.json(self.output/"geometry/parts.json")
        self.file(self.output/"geometry/scene.blend")
        self.check("geometry_recipe_sha",parts.get("recipe_sha256")==sha(self.recipe_path))
        renderer=ROOT/"Tools/PerfectPixelUniform/cabinet_geometry06.py"
        self.file(renderer)
        self.check("geometry_code_sha",parts.get("renderer_sha256")==sha(renderer))
        self.check("geometry_no_source_image",parts.get("source_image_read") is False)
        self.check("geometry_no_mesh_scale",parts.get("no_uniform_or_nonuniform_mesh_scale") is True)
        specs=parts["variants"]
        self.check("exact_variant_counts",[v["count"] for v in specs]==recipe["variants"]==[2,3])
        self.module_geometry(recipe,specs)
        for spec in specs: self.variant(spec["count"],recipe,spec,flat)
        self.file(self.output/"pixels/comparison-x4.png")
        for path in (COMMON,Path(__file__)):
            self.file(path)
        self.check("source_still_unchanged",sha(ROOT/recipe["source"])==recipe["source_sha256"])

    def report(self):
        return {"schema":"parametric-cabinet-independent-audit/6",
                "passed":bool(self.checks) and all(c["passed"] for c in self.checks),
                "checks":self.checks,"observations":self.observations,"files_sha256":self.files,
                "scope":"Saved native PNG, material provenance, semantic geometry, visibility, edges and integer display only",
                "not_verified":["aesthetic approval","99 percent source reconstruction","unique hidden-dimension recovery",
                                "Unity import/display","general furniture generator"],
                "elapsed_seconds":time.perf_counter()-self.started}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,default=ROOT/"docs/artifacts/building37/Parametric06")
    parser.add_argument("--recipe",type=Path,default=ROOT/"Tools/PerfectPixelUniform/recipe06.json")
    args=parser.parse_args(); report_path=args.output/"validation.json"
    if report_path.exists(): raise FileExistsError("Existing validation evidence is immutable")
    audit=Audit(args.output.resolve(),args.recipe.resolve())
    try: audit.run()
    except Exception as error:
        audit.check("validation_exception",False,{"type":type(error).__name__,"message":str(error)})
    result=audit.report(); write(report_path,result)
    print(json.dumps({"passed":result["passed"],"checks":len(result["checks"]),
                      "failed":[c["check"] for c in result["checks"] if not c["passed"]],
                      "report":str(report_path.resolve())}))
    if not result["passed"]: sys.exit(1)


if __name__=="__main__":
    main()
