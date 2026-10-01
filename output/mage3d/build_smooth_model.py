"""Smooth interpretation of mage2.bmp. One pixel = 1/32 units; depth is inferred.
Requires numpy + Pillow. Changes no game files. Regenerates GLB/OBJ/viewer data.
"""
from pathlib import Path
import json, math, struct
from collections import defaultdict
import numpy as np
from PIL import Image, ImageDraw
OUT=Path(__file__).resolve().parent
meshes={}; TAU=math.tau

def material(color,roughness=.85,metallic=0,emission=0):
    rgb=[v/255/12.92 if v/255<=.04045 else ((v/255+.055)/1.055)**2.4 for v in color]
    m=dict(pbrMetallicRoughness=dict(baseColorFactor=rgb+[1],metallicFactor=metallic,roughnessFactor=roughness),doubleSided=True)
    if emission:m['emissiveFactor']=[v*emission for v in rgb]
    return m
materials={'Cloth':material((131,142,152)),'Cloth_edge':material((97,105,112)),
    'Face_shadow':material((23,24,22),1),'Golden_eyes':material((208,184,0),.38,emission=.65),
    'Wood':material((144,105,43),.7),'Socket':material((200,145,59),.4,.28),
    'Crystal':material((97,217,217),.17,.12,.17)}

def surface(name,points,mat,wrap=True,reverse=False):
    points=np.array(points,dtype=float)/32;rows,cols,_=points.shape
    vertices=points.reshape(-1,3);indices=[]
    for r in range(rows-1):
        for c in range(cols if wrap else cols-1):
            a=r*cols+c;b=r*cols+(c+1)%cols;d=(r+1)*cols+c;e=(r+1)*cols+(c+1)%cols
            for tri in ((a,b,e),(a,e,d)):
                if reverse:tri=tri[::-1]
                if np.linalg.norm(np.cross(vertices[tri[1]]-vertices[tri[0]],vertices[tri[2]]-vertices[tri[0]]))>1e-12:indices.append(tri)
    normals=np.zeros_like(vertices)
    for a,b,c in indices:
        n=np.cross(vertices[b]-vertices[a],vertices[c]-vertices[a]);normals[a]+=n;normals[b]+=n;normals[c]+=n
    groups=defaultdict(list)
    for i,p in enumerate(vertices):groups[tuple(np.round(p,7))].append(i)
    for group in groups.values():normals[group]=normals[group].sum(axis=0)
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    meshes[name]=dict(vertices=vertices,normals=normals,indices=np.array(indices,dtype=np.uint32),material=mat)

def interp(y,knots,col):return float(np.interp(y,[p[0] for p in knots],[p[col] for p in knots]))
hood_profile=[(9.4,7.6,5.3),(10.2,10.1,6.6),(11.6,12.9,8.2),(12.7,13.1,8.5),(14,11.2,7.7),(16,9.4,6.8),(19,7,5.7),(22,4.65,4),(25,2.25,2.1),(27.6,.45,.55),(28,.015,.015)]
def hood_dims(y):return interp(y,hood_profile,1),interp(y,hood_profile,2)
def hood_z(x,y):
    rx,rz=hood_dims(y)
    return rz*math.sqrt(max(0,1-(x/rx)**2))-.07*(y-12)
face_center=13.65;face_height=3.65;face_width=9.4
def face_half(y):return face_width*math.sqrt(max(0,1-((y-face_center)/face_height)**2))
def face_z(x,y):
    edge=face_half(y)
    if edge<1e-6:return hood_z(0,y)
    return hood_z(x,y)-1.65*(1-(x/edge)**2)*math.sqrt(max(0,1-((y-face_center)/face_height)**2))

# Continuous hood, with a recessed opening and no cubes or pixel texture.
ys=sorted(set(np.linspace(9.4,28,95).tolist()+[face_center-face_height,face_center+face_height]+[p[0] for p in hood_profile]))
hood=[]
for y in ys:
    rx,rz=hood_dims(y);a=math.asin(min(.999,face_half(y)/rx)) if abs(y-face_center)<face_height else 0
    ring=[]
    for t in np.linspace(a,TAU-a,97):
        fold=.32*math.sin(5*t+.11*y)*min(1,(28-y)/8)*min(1,abs(math.sin(t))*2)
        ring.append(((rx+fold)*math.sin(t),y,(rz+fold*.5)*math.cos(t)-.07*(y-12)))
    hood.append(ring)
surface('Hood',hood,'Cloth',wrap=False)
face=[]
for a in np.linspace(-math.pi/2,math.pi/2,49):
    y=face_center+face_height*math.sin(a);w=face_width*math.cos(a)
    face.append([(x,y,face_z(x,y)) for x in np.linspace(-w,w,49)])
surface('Recessed_face',face,'Face_shadow',wrap=False)

def tube(name,path,radii,mat,segments=16,closed=False):
    points=np.array(path,dtype=float);grid=[]
    for i,p in enumerate(points):
        tangent=points[(i+1)%len(points)]-points[(i-1)%len(points)] if closed else points[min(i+1,len(points)-1)]-points[max(0,i-1)]
        tangent/=np.linalg.norm(tangent);ref=np.array([0.,0.,1.]) if abs(tangent[2])<.9 else np.array([0.,1.,0.])
        u=np.cross(tangent,ref);u/=np.linalg.norm(u);v=np.cross(tangent,u)
        radius=radii[i] if hasattr(radii,'__len__') else radii
        grid.append([p+radius*(math.cos(t)*u+math.sin(t)*v) for t in np.linspace(0,TAU,segments,endpoint=False)])
    if closed:grid.append(grid[0])
    surface(name,grid,mat)
rim=[]
for t in np.linspace(0,TAU,128,endpoint=False):
    x=face_width*math.cos(t);y=face_center+face_height*math.sin(t);rim.append((x,y,hood_z(x,y)+.04))
tube('Hood_opening_seam',rim,.33,'Cloth_edge',12,True)

robe_profile=[(.5,13.65,8.6),(1.2,13.9,8.8),(2.5,13.1,8.4),(5,11.5,7.6),(7.5,9.6,6.8),(10,7.7,5.6),(11.5,6.8,4.9)]
robe=[]
for y in np.linspace(.5,11.5,70):
    rx=interp(y,robe_profile,1);rz=interp(y,robe_profile,2);row=[]
    for t in np.linspace(0,TAU,112,endpoint=False):
        folds=(.72*math.cos(7*t+.15*y)+.23*math.cos(11*t-.22*y))*min(1,(12-y)/5)
        folds+=.35*math.exp(-((y-(4+.6*math.sin(3*t)))/.7)**2)
        hem=.19*math.cos(7*t)*max(0,1-(y-.5)/2)
        row.append(((rx+folds)*math.sin(t),y+hem,(rz+folds*.65)*math.cos(t)-.4))
    robe.append(row)
surface('Robe',robe,'Cloth')
surface('Robe_bottom',[[[0,.45,-.4]]*112,robe[0]],'Cloth_edge')
tube('Robe_hem',[(p[0],p[1]+.2,p[2]) for p in robe[0]],.14,'Cloth_edge',8,True)

def ellipsoid(name,center,scale,mat,segments=64,rings=40):
    grid=[]
    for a in np.linspace(-math.pi/2,math.pi/2,rings+1):
        grid.append([(center[0]+scale[0]*math.cos(a)*math.sin(t),center[1]+scale[1]*math.sin(a),center[2]+scale[2]*math.cos(a)*math.cos(t)) for t in np.linspace(0,TAU,segments,endpoint=False)])
    surface(name,grid,mat)
for x,name in [(-2.15,'Eye_left'),(2.15,'Eye_right')]:
    ellipsoid(name,(x,12.9,face_z(x,12.9)+.28),(.94,2.25,.32),'Golden_eyes',40,28)
bottom=np.array([-7.7,.9,10.3]);orb=np.array([11.2,23.9,10.7]);axis=orb-bottom;axis/=np.linalg.norm(axis);socket=orb-axis*3.9
staff_path=[];staff_radius=[]
for t in np.linspace(0,1,44):
    p=bottom+(socket-bottom)*t;p[2]+=.18*math.sin(t*math.pi);staff_path.append(p);staff_radius.append(1.32+.15*math.sin(t*4+.3))
tube('Staff',staff_path,staff_radius,'Wood',32)
ellipsoid('Staff_end',bottom,(1.3,1.3,1.3),'Wood',32,20)
tube('Orb_socket',[socket+axis*t for t in (-1.25,-.9,-.4,0,.65,1.05)],[1.5,1.75,2,2.3,2.65,2.6],'Socket',48)
ellipsoid('Crystal',orb,(4.25,4.55,4.25),'Crystal',80,56)

binary=bytearray();accessors=[];buffer_views=[]
def accessor(data,kind,component=5126,target=34962,bounds=False):
    array=np.asarray(data,dtype='<f4' if component==5126 else '<u4')
    while len(binary)%4:binary.append(0)
    offset=len(binary);blob=array.tobytes();binary.extend(blob)
    buffer_views.append(dict(buffer=0,byteOffset=offset,byteLength=len(blob),target=target))
    item=dict(bufferView=len(buffer_views)-1,componentType=component,count=len(array),type=kind)
    if bounds:item.update(min=array.min(axis=0).tolist(),max=array.max(axis=0).tolist())
    accessors.append(item);return len(accessors)-1
gltf_meshes=[];viewer=[];material_names=list(materials)
for name,m in meshes.items():
    pa=accessor(m['vertices'],'VEC3',bounds=True);na=accessor(m['normals'],'VEC3');ia=accessor(m['indices'].ravel(),'SCALAR',5125,34963)
    gltf_meshes.append(dict(name=name,primitives=[dict(attributes={'POSITION':pa,'NORMAL':na},indices=ia,material=material_names.index(m['material']),mode=4)]))
    mat=materials[m['material']];pbr=mat['pbrMetallicRoughness']
    viewer.append(dict(name=name,positions=np.round(m['vertices'],6).ravel().tolist(),normals=np.round(m['normals'],5).ravel().tolist(),indices=m['indices'].ravel().tolist(),color=pbr['baseColorFactor'][:3],roughness=pbr['roughnessFactor'],emission=mat.get('emissiveFactor',[0,0,0])))
gltf=dict(asset={'version':'2.0','generator':'Grimorium smooth mage reconstruction'},scene=0,
    scenes=[{'nodes':[0]}],nodes=[{'name':'Mage','children':list(range(1,len(meshes)+1))}]+[{'name':n,'mesh':i} for i,n in enumerate(meshes)],
    meshes=gltf_meshes,materials=[dict(name=k,**v) for k,v in materials.items()],accessors=accessors,bufferViews=buffer_views,buffers=[{'byteLength':len(binary)}])
js=json.dumps(gltf,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
glb=struct.pack('<4sII',b'glTF',2,28+len(js)+len(binary))+struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(binary),b'BIN\0')+binary
(OUT/'mage.glb').write_bytes(glb)
with (OUT/'mage.mtl').open('w') as f:
    for name,mat in materials.items():
        rgb=' '.join(f'{v:.6f}' for v in mat['pbrMetallicRoughness']['baseColorFactor'][:3]);f.write(f'newmtl {name}\nKd {rgb}\nKa 0.1 0.1 0.1\nKs 0.2 0.2 0.2\nNs 30\nillum 2\n\n')
with (OUT/'mage.obj').open('w') as f:
    f.write('mtllib mage.mtl\n');offset=1
    for name,m in meshes.items():
        f.write(f'o {name}\nusemtl {m["material"]}\ns 1\n')
        for p in m['vertices']:f.write('v '+' '.join(f'{v:.6f}' for v in p)+'\n')
        for n in m['normals']:f.write('vn '+' '.join(f'{v:.6f}' for v in n)+'\n')
        for tri in m['indices']:f.write('f '+' '.join(f'{i+offset}//{i+offset}' for i in tri)+'\n')
        offset+=len(m['vertices'])
(OUT/'model_data.js').write_text('window.MAGE_MODEL='+json.dumps(viewer,separators=(',',':'))+';\n')

def srgb(rgb):return tuple(int(np.clip((12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055)*255,0,255)) for v in rgb)
def render(yaw,filename):
    yaw=math.radians(yaw);pitch=math.radians(9);right=np.array([math.cos(yaw),0,-math.sin(yaw)])
    forward=np.array([math.sin(yaw)*math.cos(pitch),math.sin(pitch),math.cos(yaw)*math.cos(pitch)]);up=np.cross(forward,right)
    center=np.array([0,.44,.03]);tris=[];light=np.array([-.45,.75,.9]);light/=np.linalg.norm(light)
    for m in meshes.values():
        mat=materials[m['material']];base=np.array(mat['pbrMetallicRoughness']['baseColorFactor'][:3]);em=np.array(mat.get('emissiveFactor',[0,0,0]))
        for ids in m['indices']:
            points=m['vertices'][ids]-center;n=np.mean(m['normals'][ids],axis=0);n/=max(np.linalg.norm(n),1e-9)
            projected=[(360+np.dot(p,right)*590,366-np.dot(p,up)*590) for p in points]
            lit=.38+.65*max(0,np.dot(n,light))+.12*max(0,np.dot(n,[-.7,.2,-.8]));halfv=light+forward;halfv/=np.linalg.norm(halfv)
            rough=mat['pbrMetallicRoughness']['roughnessFactor']
            spec=max(0,np.dot(n,halfv))**(8+70*(1-rough))*.25*(1-rough)
            tris.append((float(np.mean(points@forward)),projected,srgb(base*lit+em+spec)))
    canvas=Image.new('RGB',(720,720),(28,35,40));draw=ImageDraw.Draw(canvas)
    for _,points,color in sorted(tris,key=lambda t:t[0]):draw.polygon(points,fill=color)
    canvas.resize((600,600),Image.Resampling.LANCZOS).save(OUT/filename)
render(0,'preview-front.png');render(35,'preview-angle.png');render(180,'preview-back.png')
print('Created smooth mage.glb, mage.obj + mage.mtl and model_data.js')
print('Triangles:',sum(len(m['indices']) for m in meshes.values()),'GLB bytes:',len(glb))
