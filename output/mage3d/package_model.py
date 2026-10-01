"""Bundle the model and offline viewer without changing any game files."""
from pathlib import Path
import base64, io, zipfile
from PIL import Image
folder=Path(__file__).resolve().parent
source=folder.parents[1]/'assets/images/player/mage2.bmp'
reference=Image.open(source if source.exists() else folder/'reference.png')
png=io.BytesIO();reference.save(png,format='PNG')
(folder/'reference.png').write_bytes(png.getvalue())
script=(folder/'model_data.js').read_text()
script+='\nwindow.MAGE_GLB="'+base64.b64encode((folder/'mage.glb').read_bytes()).decode()+'";'
script+='\nwindow.MAGE_REFERENCE="data:image/png;base64,'+base64.b64encode(png.getvalue()).decode()+'";'
page=(folder/'viewer-template.html').read_text(encoding='utf-8').replace('/*MODEL_DATA*/',script)
(folder/'mage-viewer.html').write_text(page,encoding='utf-8')
with zipfile.ZipFile(folder/'mage-3d.zip','w',compression=zipfile.ZIP_DEFLATED) as archive:
    for name in ['mage.glb','mage.obj','mage.mtl','mage-viewer.html','LEEME.txt','reference.png','build_smooth_model.py','package_model.py','viewer-template.html']:
        archive.write(folder/name,'mage3d/'+name)
print('Ready: mage-viewer.html and mage-3d.zip')
