"""Deterministic desk production units consumed by the existing WorkLoop graph."""
import argparse
import html
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont

from common import ROOT,BLENDER,read,write,sha,resolve,basis,gap_coefficient,gap_aperture,linear,srgb,passdir,receipt,verify_receipt,consistent_edges,parallel_double_strokes

def stage_resources(stage,pass_index,run_dir,contract_path):
    run=Path(run_dir);p=passdir(run,pass_index);c=read(contract_path)
    reads=[Path(contract_path)];writes=[]
    if stage=='inputs':
        reads += [resolve(c['source_blend']),resolve(c['source_wood'])]
        writes=[run/'inputs',passdir(run,0)/'settings.json']
    elif stage=='geometry':reads += [run/'inputs',resolve(c['source_blend'])];writes=[run/'geometry']
    elif stage=='material':reads += [run/'inputs',resolve(c['source_wood'])];writes=[run/'material']
    elif stage=='raster':
        reads += [run/'geometry',p/'settings.json'];writes=[p/'raster']
        if pass_index:reads += [passdir(run,pass_index-1)/'raster',passdir(run,pass_index-1)/'settings.json']
    elif stage=='shade':
        reads += [p/'raster',run/'material',p/'settings.json'];writes=[p/'shade']
        if pass_index:reads += [passdir(run,pass_index-1)/'shade',passdir(run,pass_index-1)/'settings.json']
    elif stage=='pixel':reads += [p/'raster',p/'shade'];writes=[p/'pixel']
    elif stage=='diagnose':reads += [run/'inputs',run/'geometry',run/'material',p/'raster',p/'shade',p/'pixel'];writes=[p/'diagnose']
    elif stage=='repair':reads += [passdir(run,pass_index-1)/'diagnose',passdir(run,pass_index-1)/'settings.json',run/'geometry'];writes=[p/'settings.json',p/'repair']
    elif stage=='package':reads += [run/'material',p/'raster',p/'shade',p/'pixel',p/'diagnose',passdir(run,0)/'pixel',passdir(run,0)/'diagnose'];writes=[p/'package']
    elif stage=='validate':reads += [run/'inputs',run/'geometry',run/'material',p/'raster',p/'shade',p/'pixel',p/'diagnose',p/'package'];writes=[p/'validate']
    else:raise ValueError(stage)
    return {'reads':reads,'writes':writes}

def blender(stage,out,contract,geometry=None,settings=None):
    argv=[str(BLENDER),'--background','--factory-startup','--python',str(Path(__file__).with_name('blender_stage.py')),
          '--','--stage',stage,'--contract',str(contract),'--output',str(out)]
    if geometry:argv += ['--geometry',str(geometry)]
    if settings:argv += ['--settings',str(settings)]
    # The graph bounds this command to60s. This local subprocess has its own shorter bound.
    result=subprocess.run(argv,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=50)
    (out/'blender.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    if result.returncode:raise RuntimeError(f'Blender failed: {result.returncode}; {out}/blender.log')

def diagnostic(code,stage,measured,expected,unit,repairable=False,parts=None):
    return {'code':code,'owner_stage':stage,'measured':measured,'expected':expected,'unit':unit,
            'repairable':repairable,'parts':parts or []}

def reuse_stage(stage,index,run,contract_path):
    """Only the registered stroke correction may reuse immutable geometric/shade buffers."""
    p=passdir(run,index);settings=read(p/'settings.json');source_index=settings.get('reuse_pass')
    if source_index is None:return None
    if source_index!=index-1:raise ValueError('Cache must refer to the immediately diagnosed pass')
    prev=passdir(run,source_index);old=read(prev/'settings.json')
    if settings['drawer_gap_override']!=old['drawer_gap_override']:raise ValueError('Geometry changed; cache reuse forbidden')
    previous=verify_receipt(prev/stage/'stage_receipt.json')
    if previous['inputs'].get(str(Path(contract_path).resolve()))!=sha(contract_path):raise ValueError('Cache contract differs')
    names={'raster':['buffers.npz','raster.json','desk.blend'],
           'shade':['shade.npz','shade.json','before_edges.png']}[stage]
    out=p/stage;out.mkdir(parents=True)
    for name in names:shutil.copy2(prev/stage/name,out/name)
    result={'state':'ready','stage':stage,'pass':index,'reused_from_pass':source_index,
            'algorithm_executed':False,'reason':'pixel boundary implementation correction only'}
    inp=[contract_path,p/'settings.json',prev/stage/'stage_receipt.json']+[prev/stage/name for name in names]
    receipt(out,stage,inp,[out/name for name in names],result)
    return result

def execute(stage,index,run,contract_path):
    c=read(contract_path);p=passdir(run,index)
    out=run/stage if stage in ('inputs','geometry','material') else p/stage
    if out.exists():raise ValueError(f'Output already exists; resume graph, do not overwrite: {out}')
    start=time.perf_counter();result={'state':'ready','stage':stage,'pass':index}
    if stage in ('raster','shade'):
        reused=reuse_stage(stage,index,run,contract_path)
        if reused is not None:return reused
    inp=[];outputs=[]
    if stage=='inputs':
        source=resolve(c['source_blend']);wood=resolve(c['source_wood'])
        if sha(wood)!=c['source_wood_sha256']:
            return {'state':'blocked','diagnosis':diagnostic('UNAPPROVED_MATERIAL_SOURCE','material',sha(wood),c['source_wood_sha256'],'sha256')}
        if c['lighting']['source']!='geometry_normal_and_shadow_ray':
            return {'state':'blocked','diagnosis':diagnostic('SHADED_TEXTURE_CANNOT_REPLACE_LIGHTING','shade',c['lighting']['source'],'geometry_normal_and_shadow_ray','method')}
        if len(c['lighting']['thresholds'])!=2 or len(c['lighting']['linear_gains'])!=3:raise ValueError('Exactly3 shading bands required')
        out.mkdir(parents=True)
        write(out/'inputs.json',{'source_blend_sha256':sha(source),'source_wood_sha256':sha(wood),
             'contract_sha256':sha(contract_path),'scope':'Actual geometry + approved flat material; no desk-color reprojection'})
        write(passdir(run,0)/'settings.json',{'drawer_gap_override':None,'repair_history':[]})
        inp=[contract_path,source,wood];outputs=[out/'inputs.json',passdir(run,0)/'settings.json']
    elif stage=='geometry':
        blender(stage,out,contract_path)
        g=read(out/'geometry.json');inp=[contract_path,resolve(c['source_blend'])];outputs=[out/'scene.blend',out/'geometry.json']
        result['checks']=g['checks']
    elif stage=='material':
        from material import prepare_material
        data=prepare_material(resolve(c['source_wood']),out,{key:c['material'][key] for key in ('grid','levels')})
        result['material_shape']=data['shape'];result['perfectpixel']=data['perfectpixel']
        inp=[contract_path,resolve(c['source_wood'])]
        outputs=[out/name for name in ['normalized.png','grain.npy','palette.json','receipt.json']]
    elif stage=='raster':
        blender(stage,out,contract_path,run/'geometry',p/'settings.json')
        inp=[contract_path,run/'geometry/scene.blend',p/'settings.json']
        outputs=[out/name for name in ['buffers.npz','raster.json','desk.blend']]
        result['size']=read(out/'raster.json')['size']
    elif stage=='shade':
        out.mkdir(parents=True)
        b=np.load(p/'raster/buffers.npz');m=b['mask'];n=b['normals'];positions=b['positions']
        light=np.array(c['lighting']['to_light'],float);light/=np.linalg.norm(light)
        diffuse=np.maximum(0,n@light)
        band=np.digitize(diffuse*b['visibility'],c['lighting']['thresholds']).astype('uint8')
        grain=np.load(run/'material/grain.npy');gh,gw=grain.shape
        texel=c['material']['texel_meters'];raster=read(p/'raster/raster.json')
        sample_u=np.zeros_like(diffuse);sample_v=np.zeros_like(diffuse)
        # Oriented world-space wood coordinates, with a common physical texel size.
        for part in raster['parts']:
            area=b['part']==part['id'];axis=np.argmax(np.abs(n),axis=2)
            for face_axis in range(3):
                q=area&(axis==face_axis)
                if part['role']=='leg' and face_axis!=2:
                    sample_u[q]=positions[...,2][q]/texel
                    cross=0 if face_axis==1 else 1;sample_v[q]=positions[...,cross][q]/texel
                else:
                    axes=([1,2],[0,2],[0,1])[face_axis]
                    sample_u[q]=positions[...,axes[0]][q]/texel
                    sample_v[q]=positions[...,axes[1]][q]/texel
        iu=np.floor(sample_u).astype(int)%gw;iv=np.floor(-sample_v).astype(int)%gh
        gi=grain[iv,iu];material_palette=np.array(read(run/'material/palette.json')['colors_srgb8'])
        palette=srgb(linear(material_palette)[None,:,:]*np.array(c['lighting']['linear_gains'])[:,None,None])
        colors=palette[band,gi];rgba=np.dstack((colors,m.astype('uint8')*255));rgba[~m]=0
        np.savez_compressed(out/'shade.npz',band=band,grain=gi,rgba=rgba,palette=palette,diffuse=diffuse)
        Image.fromarray(rgba).save(out/'before_edges.png')
        write(out/'shade.json',{'method':'normal_dot_direction_times_shadow_visibility_then_3_band_palette',
                               'palette_srgb8':palette.tolist(),'band_counts':np.bincount(band[m],minlength=3).tolist(),
                               'grain_counts':np.bincount(gi[m],minlength=4).tolist(),'baked_desk_rgb_used':False})
        inp=[contract_path,p/'raster/buffers.npz',run/'material/grain.npy',run/'material/palette.json']
        outputs=[out/'shade.npz',out/'shade.json',out/'before_edges.png']
    elif stage=='pixel':
        out.mkdir(parents=True);b=np.load(p/'raster/buffers.npz');s=np.load(p/'shade/shade.npz')
        edges,records,policies=consistent_edges(b,c['camera'])
        rgba=s['rgba'].copy();rgba[edges,:3]=c['pixel']['outline_srgb8'];rgba[~b['mask']]=0
        np.savez_compressed(out/'edges.npz',edges=edges,edge_records=records)
        image=Image.fromarray(rgba);image.save(out/'desk.png')
        scale=c['pixel']['preview_scale'];image.resize((image.width*scale,image.height*scale),Image.Resampling.NEAREST).save(out/'desk_preview.png')
        # Observable component images use the exact same native geometry samples.
        nm=np.dstack(((b['normals']*.5+.5)*255,b['mask']*255)).astype('uint8');nm[~b['mask']]=0
        Image.fromarray(nm).save(out/'normals.png')
        shadow=np.dstack([np.where(b['visibility'],220,45)]*3+[b['mask']*255]).astype('uint8');shadow[~b['mask']]=0
        Image.fromarray(shadow).save(out/'visibility.png')
        write(out/'pixel.json',{'size':list(image.size),'native_pixel_rays':True,'finished_rgb_downsampled':False,
              'palette_count':len(np.unique(rgba[b['mask'],:3],axis=0)),
              'alpha_values':np.unique(rgba[...,3]).tolist(),'outline_pixels':int(edges.sum()),
              'edge_policy':'consistent_visible_surface_pair','surface_pairs':policies})
        inp=[contract_path,p/'raster/buffers.npz',p/'shade/shade.npz'];outputs=[out/name for name in ['desk.png','desk_preview.png','normals.png','visibility.png','pixel.json','edges.npz']]
    elif stage=='diagnose':
        out.mkdir(parents=True);raster=read(p/'raster/raster.json');base=read(run/'geometry/geometry.json')
        a=np.asarray(Image.open(p/'pixel/desk.png').convert('RGBA'));b=np.load(p/'raster/buffers.npz');s=np.load(p/'shade/shade.npz')
        issues=[];required=c['pixel']['minimum_gap_pixels']
        front_depth=next(q['dimensions'][1] for q in raster['parts'] if q['name']=='Drawer_-1')
        aperture=gap_aperture(raster['drawer_gap'],front_depth,c['camera'],required)
        width=aperture['clear_width_pixels'];target=aperture['required_gap_m']
        fixable=bool(target<=base['drawer_span']*c['repair']['max_gap_fraction_of_span'])
        if width+1e-5<required:
            issues.append(diagnostic('DRAWER_GAP_UNDERSAMPLED','geometry',float(width),required,'px',bool(fixable),['Drawer_-1','Drawer_1','Handle_-1','Handle_1']))
        checks=dict(raster['geometry_checks'])
        checks['gap_is_visible_behind_fronts']=all(owner not in raster['drawer_ids'] for owner in raster['gap_ray_owners'])
        checks['finite_ray_matches_independent_boxes']=all(x['same_owner'] and x['depth_error']<1e-4 for x in raster['slab_checks'])
        checks['hard_alpha']=set(np.unique(a[...,3])).issubset({0,255})
        allowed={tuple(x) for x in s['palette'].reshape(-1,3)}|{tuple(c['pixel']['outline_srgb8'])}
        checks['declared_palette_only']=all(tuple(x) in allowed for x in np.unique(a[b['mask'],:3],axis=0))
        checks['actual_3d_shadows_present']=raster['shadow_pixels']>0
        checks['shading_and_grain_separate']=s['band'].max()<=2 and s['grain'].max()<=3
        edge_data=np.load(p/'pixel/edges.npz') if (p/'pixel/edges.npz').exists() else b
        records=edge_data['edge_records'];checks['outline_owner_matches_visible_pixel']=all(int(b['part'][y,x])==obj and int(b['face'][y,x])==face for y,x,obj,face in records)
        ink=(a[...,:3]==c['pixel']['outline_srgb8']).all(axis=2)&b['mask']
        double=parallel_double_strokes(b,ink)
        checks['parallel_seam_single_side']=not double
        checks={key:bool(value) for key,value in checks.items()}
        # Ambiguous finite junctions are skipped and reported, never assigned to a hidden surface.
        for key,value in checks.items():
            if not value:
                if key=='parallel_seam_single_side':
                    issues.append(diagnostic('BOUNDARY_DOUBLE_STROKE','pixel',sum(q['count'] for q in double),0,'interior adjacent pixel pairs',True,double))
                elif key=='gap_is_visible_behind_fronts' and width+1e-5<required:
                    issues.append(diagnostic('DRAWER_GAP_OCCLUDED','geometry',raster['gap_ray_owners'],'owner behind front drawers','part_id',fixable,['Drawer_-1','Drawer_1']))
                else:issues.append(diagnostic(key,'raster' if 'ray' in key or 'visible' in key else 'pixel',False,True,'boolean'))
        status='blocked' if any(not x['repairable'] for x in issues) else ('repairable' if issues else 'ready')
        result.update(state=status,issues=issues,checks=checks,drawer_gap_pixels=width,aperture=aperture,
          skipped_boundary_junctions=raster['finite_boundary_ambiguous'],
          unjudged=['그림체·색감·나뭇결 크기의 만족도','기준 생성 이미지와99%외형 재현'])
        adjacent_ink=0
        for axis in (0,1):
            first=(slice(None,-1),slice(None)) if axis==0 else (slice(None),slice(None,-1))
            second=(slice(1,None),slice(None)) if axis==0 else (slice(None),slice(1,None))
            adjacent_ink+=int((ink[first]&ink[second]&(b['part'][first]!=b['part'][second])&b['mask'][first]&b['mask'][second]).sum())
        result['boundary_observations']={'skipped_finite_junctions':raster['finite_boundary_ambiguous'],
                                        'adjacent_cross_part_ink_pairs':adjacent_ink,
                                        'interior_parallel_double_strokes':double,
                                        'global_one_pixel_stroke_proven':False}
        write(out/'diagnosis.json',result)
        inp=[contract_path,p/'raster/raster.json',p/'raster/buffers.npz',p/'shade/shade.npz',p/'pixel/desk.png']
        outputs=[out/'diagnosis.json']
    elif stage=='repair':
        out.mkdir(parents=True);prev=passdir(run,index-1);old=read(prev/'settings.json');diag=read(prev/'diagnose/diagnosis.json');base=read(run/'geometry/geometry.json')
        codes={i['code'] for i in diag['issues']}
        if not codes or codes-{'DRAWER_GAP_UNDERSAMPLED','DRAWER_GAP_OCCLUDED','BOUNDARY_DOUBLE_STROKE'}:raise ValueError('No registered repair for this diagnosis')
        settings=dict(old);settings.pop('reuse_pass',None)
        if codes=={'BOUNDARY_DOUBLE_STROKE'}:
            record={'code':'BOUNDARY_DOUBLE_STROKE','owner_stage':'pixel',
                    'old_method':'independent boundary midpoint owner',
                    'new_method':'consistent visible surface pair stroke',
                    'reuse':['raster','shade'],'unchanged':['geometry','material','camera','lighting'],
                    'scope':'implementation defect correction; no design parameter changed'}
            settings['reuse_pass']=index-1
        else:
            if 'common_drawer_gap' not in c['repair']['allowed']:raise ValueError('Gap repair is not authorized by the contract')
            front_depth=next(q['dimensions'][1] for q in base['parts'] if q['name']=='Drawer_-1')
            target=gap_aperture(base['drawer_gap'],front_depth,c['camera'],c['pixel']['minimum_gap_pixels'])['required_gap_m']
            if target>base['drawer_span']*c['repair']['max_gap_fraction_of_span']:raise ValueError('Repair exceeds declared style bound')
            record={'code':'DRAWER_GAP_UNDERSAMPLED','old_gap_m':base['drawer_gap'] if old['drawer_gap_override'] is None else old['drawer_gap_override'],
                    'new_gap_m':target,'fixed_ppu':c['camera']['pixels_per_meter'],
                    'formula':'g*=front_depth*abs(tan(phi)) + required_px/(P*abs(cos(phi))); intersect finite front/back apertures; preserve outer span; recenter both drawers and handles'}
            settings['drawer_gap_override']=target
        settings['repair_history']=old['repair_history']+[record]
        write(p/'settings.json',settings)
        write(out/'repair.json',record);result['repair']=record
        inp=[contract_path,prev/'settings.json',prev/'diagnose/diagnosis.json',run/'geometry/geometry.json']
        outputs=[p/'settings.json',out/'repair.json']
    elif stage=='package':
        out.mkdir(parents=True)
        for source,destination in [(p/'pixel/desk.png','desk.png'),(p/'pixel/desk_preview.png','desk_preview.png'),
                (p/'raster/desk.blend','desk.blend'),(p/'diagnose/diagnosis.json','diagnosis.json')]:shutil.copy2(source,out/destination)
        before=Image.open(passdir(run,0)/'pixel/desk.png').convert('RGBA');after=Image.open(p/'pixel/desk.png').convert('RGBA')
        scale=c['pixel']['preview_scale'];w,h=after.size
        board=Image.new('RGB',(w*scale*2+36,h*scale+70),(238,235,227));draw=ImageDraw.Draw(board)
        try:font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20)
        except OSError:font=ImageFont.load_default()
        for j,(im,label) in enumerate([(before,'자동 진단 전'),(after,'서랍 틈·내부 경계 수정 후')]):
            big=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
            board.paste(big,(12+j*(w*scale+12),52),big);draw.text((12+j*(w*scale+12),14),label,fill=(45,35,25),font=font)
        board.save(out/'before_after.png')
        diag=read(out/'diagnosis.json');rep=read(p/'settings.json')['repair_history'];rows=''.join(f'<tr><td>{html.escape(k)}</td><td>{v}</td></tr>' for k,v in diag['checks'].items())
        import base64
        def data(path):return 'data:image/png;base64,'+base64.b64encode(Path(path).read_bytes()).decode()
        page='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>픽셀 제작 그래프 실행 결과</title><style>body{font:16px system-ui;background:#f6f3ec;color:#29251d;margin:32px;max-width:1250px}img{image-rendering:pixelated;max-width:100%}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #bbb}.flow{line-height:2;background:#e5e0d3;padding:15px}pre{white-space:pre-wrap}</style><h1>픽셀 제작 그래프 — 실제 실행 결과</h1><p>기술 조건 통과 / 사용자 외형 판단 대기. 99% 외형 재현 성공을 뜻하지 않습니다.</p><div class="flow">입력 → 실제 메시 / 원본 PerfectPixel 재료 → 픽셀 광선 → 명암 계산 → 팔레트·가시 경계 → 진단 → 공통 틈 수선 → 하위 단계 재실행 → 제출</div>'''
        page+=f'<h2>수정 전 / 후</h2><img src="{data(out/"before_after.png")}"><h2>수학적 수정</h2><pre>{html.escape(json.dumps(rep,ensure_ascii=False,indent=2))}</pre><h2>실제 조건</h2><table>{rows}</table>'
        page+=f'<h2>법선 / 광원 가림</h2><img width="500" src="{data(p/"pixel/normals.png")}"><img width="500" src="{data(p/"pixel/visibility.png")}"><h2>분리한 목재 입력</h2><img width="450" src="{data(run/"material/normalized.png")}"><p>출처를 고정한 평면 목재이며 단일 이미지의 순수 albedo를 증명하는 기능은 아닙니다.</p>'
        (out/'report.html').write_text(page,encoding='utf-8')
        inp=[contract_path,p/'raster/desk.blend',p/'pixel/desk.png',p/'diagnose/diagnosis.json',passdir(run,0)/'pixel/desk.png']
        outputs=[out/name for name in ['desk.png','desk_preview.png','desk.blend','diagnosis.json','before_after.png','report.html']]
        result['report']=str(out/'report.html')
    elif stage=='validate':
        out.mkdir(parents=True)
        locations=[run/'inputs',run/'geometry',run/'material']
        locations += [p/x for x in ['raster','shade','pixel','diagnose','package']]
        for directory in locations:verify_receipt(directory/'stage_receipt.json')
        diag=read(p/'diagnose/diagnosis.json');raster=read(p/'raster/raster.json')
        actual=np.asarray(Image.open(p/'package/desk.png').convert('RGBA'));source=np.asarray(Image.open(p/'pixel/desk.png').convert('RGBA'))
        # Reload actual arrays; acceptance does not trust an AI boolean or file presence alone.
        palette=np.load(p/'shade/shade.npz')['palette'];mask=actual[...,3]>0
        allowed={tuple(x) for x in palette.reshape(-1,3)}|{tuple(c['pixel']['outline_srgb8'])}
        accepted=(diag['state']=='ready' and all(diag['checks'].values()) and np.array_equal(actual,source)
                  and set(np.unique(actual[...,3])).issubset({0,255})
                  and all(tuple(x) in allowed for x in np.unique(actual[mask,:3],axis=0))
                  and raster['gap_aperture']['clear_width_pixels']+1e-5>=c['pixel']['minimum_gap_pixels'])
        result.update(accepted=bool(accepted),state='ready' if accepted else 'blocked',visual_approval='pending',
                      actual_size=[actual.shape[1],actual.shape[0]],artifact=str(p/'package/desk.png'))
        write(out/'validation.json',result)
        inp=[contract_path,p/'package/desk.png',p/'raster/raster.json',p/'diagnose/diagnosis.json']
        outputs=[out/'validation.json']
    else:raise ValueError(stage)
    result['elapsed_seconds']=round(time.perf_counter()-start,4)
    receipt(out,stage,inp,outputs,result)
    return result

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    parser=argparse.ArgumentParser();parser.add_argument('--stage',required=True);parser.add_argument('--pass',dest='pass_index',type=int,default=0)
    parser.add_argument('--run-dir',required=True);parser.add_argument('--contract',required=True)
    a=parser.parse_args();run=Path(a.run_dir).resolve();contract=Path(a.contract).resolve()
    try:result=execute(a.stage,a.pass_index,run,contract)
    except Exception as e:
        print(json.dumps({'state':'blocked','stage':a.stage,'error':str(e)},ensure_ascii=False));return 1
    print(json.dumps(result,ensure_ascii=False));return 0

if __name__=='__main__':sys.exit(main())
