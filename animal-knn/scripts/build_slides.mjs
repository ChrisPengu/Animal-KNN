// Run with the Codex bundled Node runtime. ARTIFACT_TOOL_PATH and PRESENTATION_SKILL_DIR can override the installed paths.
import fs from 'node:fs/promises';
import {readFileSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const workspaceDir=root;
const runtime=process.env.CODEX_ARTIFACT_RUNTIME || 'C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1123-915-0_26.1123.915.0_x64__3k8sg7r9htsxt/dependencies';
process.env.RUNTIME_NODE_MODULES ||= `${runtime}/node/node_modules`;
const SKILL_DIR=process.env.PRESENTATION_SKILL_DIR || 'C:/Users/MSI/.codex/plugins/cache/openai-primary-runtime/presentations/26.1123.11515/skills/presentations';
const {Presentation,PresentationFile}=await import(pathToFileURL(process.env.ARTIFACT_TOOL_PATH || `${runtime}/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs`).href);
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL_DIR,'container_tools/artifact_tool_utils.mjs')).href);
const d=JSON.parse(await fs.readFile(path.join(root,'reports/deck_data.json'),'utf8'));
const build=path.join(workspaceDir,'.cache/slides');
await fs.mkdir(build,{recursive:true});
const presentation=Presentation.create({slideSize:{width:1280,height:720}});
const ink='#18352A',green='#176B45',muted='#496457',light='#E6F0EA';
const font='Arial';
const pct=x=>(x*100).toFixed(2)+'%';
function photoSource(filename){
  const source=d.photo_sources?.[filename];
  return source?`Nguồn ảnh: ${source.source_page}\nTác giả: ${source.author}\nGiấy phép: ${source.license} ${source.license_url}`:`Nguồn ảnh: ${filename}, xem data/external/manifest.csv`;
}
function text(slide,value,left,top,width,height,size=22,bold=false,color=ink){
  const shape=slide.shapes.add({geometry:'textbox',position:{left,top,width,height},fill:'none',line:{fill:'none',width:0}});
  shape.text=String(value);shape.text.style={fontFamily:font,fontSize:`${size}pt`,bold,color};return shape;
}
function page(title,notes=''){
  const slide=presentation.slides.add();slide.background.fill='#FFFFFF';
  text(slide,title,64,36,1152,90,32,true);
  text(slide,'Animal K-NN · STL-10, sáu nhóm',64,674,1000,26,11,false,muted);
  text(slide,String(presentation.slides.items.length).padStart(2,'0'),1170,674,46,26,11,false,muted);
  slide.speakerNotes.text=notes;return slide;
}
function lines(slide,items,left=64,top=170,width=1120,size=23,spacing=90){
  items.forEach((value,i)=>text(slide,value,left,top+i*spacing,width,spacing-8,size));
}
function table(slide,values,left=64,top=170,width=1152,height=410,size=19){
  const t=slide.tables.add({rows:values.length,columns:values[0].length,left,top,width,height,values});
  t.borders.assign({style:'solid',fill:'#CBDCD1',width:.8});
  for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
    const cell=t.getCell(r,c);cell.fill=r===0?green:(r%2? '#FFFFFF':'#F1F6F3');
    cell.text.style={fontFamily:font,fontSize:`${size}pt`,color:r===0?'#FFFFFF':ink,bold:r===0};
  }
  return t;
}
function chart(slide,type,config){
  const c=slide.charts.add(type,{
    position:{left:64,top:165,width:1152,height:430},
    chartFill:'#FFFFFF',plotAreaFill:'#FFFFFF',
    xAxis:{textStyle:{fontSize:20,typeface:font,fill:ink}},
    yAxis:{min:0,max:1,numberFormatCode:'0%',textStyle:{fontSize:18,typeface:font,fill:muted},majorGridlines:{fill:'#DCE6DF',width:1}},
    legend:{position:'bottom',overlay:false,textStyle:{fontSize:18,typeface:font}},
    ...config,
    series:config.series.map(series=>({...series,values:series.values.map(value=>Number(Number(value).toFixed(8)))})),
  });
  slide.speakerNotes.text+='\nGiá trị biểu đồ làm tròn 8 chữ số thập phân để tương thích Excel; CSV giữ kết quả đầy đủ.';
  applyPresentationChartFont(c,{fontFamily:font});return c;
}
function image(slide,filename,left,top,width,height,alt,crop){
  const blob=new Uint8Array(readFileSync(path.join(root,filename)));
  const contentType=filename.toLowerCase().endsWith('.png')?'image/png':'image/jpeg';
  return slide.images.add({blob,contentType,position:{left,top,width,height},fit:'contain',alt,...(crop?{crop}: {})});
}
const stl='https://cs.stanford.edu/~acoates/stl10/';

// 1
{
  const s=page('');
  text(s,'Phân loại động vật\nbằng K-NN',64,140,670,200,40,true);
  text(s,'Đặc trưng màu sắc, hình dạng\nvà đặc trưng học sâu',64,365,650,115,24);
  text(s,'Đồ án xử lý ảnh và thị giác máy tính\n18/11/2026',64,545,660,85,18,false,muted);
  image(s,'data/external/monkey/monkey_04.jpg',790,90,400,515,'Ảnh khỉ trong bộ kiểm tra Wikimedia');
  s.speakerNotes.text=photoSource('data/external/monkey/monkey_04.jpg')+'\nSố liệu trong deck lấy từ kết quả thực nghiệm cục bộ.';
}
// 2
{
  const s=page('Dữ liệu và làm sạch',`Nguồn: ${stl}. Manifest: data/processed/manifest.csv. Danh sách loại: data/curation/near_duplicate_review.csv.`);
  const active=d.counts.filter(x=>['train','val','test'].includes(x['Tập dữ liệu']));
  chart(s,'bar',{categories:d.classes_vi,series:active.map((r,i)=>({name:r['Tập dữ liệu'],values:d.classes_vi.map(n=>r[n]),fill:[green,'#9DC7AE','#5D7B99'][i]})),
    hasLegend:true,yAxis:{min:0,max:900,title:'Số ảnh',textStyle:{fontSize:18,typeface:font},majorGridlines:{fill:'#DCE6DF',width:1}}});
  text(s,'2.385 train, 595 validation, 4.800 test sau khi loại 20 ảnh gần trùng',64,609,1152,50,19);
}
// 3
{
  const s=page('Quy trình phân loại',`Nguồn: mã nguồn animal_knn/features.py, training.py và inference.py. Trọng số tiền huấn luyện: Torchvision ImageNet-1K.`);
  lines(s,['1. Chuẩn hóa ảnh RGB về 96 × 96','2. Trích vector thủ công hoặc CNN','3. PCA nếu chọn, sau đó chuẩn hóa L2','4. Tìm k láng giềng trong train','5. Bỏ phiếu và hiển thị ảnh tham chiếu'],64,156,810,23,88);
  image(s,'data/external/bird/bird_08.jpg',920,180,280,340,'Ảnh chim ngoài tập STL-10');
  s.speakerNotes.text+='\n'+photoSource('data/external/bird/bird_08.jpg');
}
// 4
{
  const s=page('Các biểu diễn đặc trưng','Nguồn: cấu hình thực thi animal_knn/features.py. HOG: scikit-image. GrabCut và Hu moments: OpenCV. Backbone: Torchvision.');
  table(s,[['Đặc trưng','Thiết lập chính','Số chiều'],['Histogram HSV','8 × 8 × 8 bins','512'],['HOG','9 hướng, cell 8 × 8','4.356'],['Hu moments','7 moments, biến đổi log','7'],['ResNet18','Pooling, bỏ lớp phân loại','512'],['EfficientNet-B0','Pooling, bỏ classifier','1.280']],64,165,1152,420,18);
  text(s,'GrabCut được đo bằng cặp thí nghiệm cùng đặc trưng, có và không tách nền',64,610,1152,45,18,false,muted);
}
// 5
{
  const s=page('Đặc trưng CNN với K-NN','Nguồn: results/validation_comparison.csv. Chọn backbone để fine-tune chỉ bằng validation, không dùng test.');
  const rows=d.comparison.filter(r=>['resnet18','efficientnet_b0'].includes(r.feature)||r.feature.endsWith('_finetuned'));
  chart(s,'bar',{categories:rows.map(r=>r.feature.endsWith('_finetuned')?'CNN fine-tune':r.feature==='resnet18'?'ResNet18':'EfficientNet-B0'),
    series:[{name:'Validation accuracy',values:rows.map(r=>r.val_accuracy),fill:green}],hasLegend:false,
    dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:18,typeface:font},numberFormatCode:'0.0%'}});
  text(s,'Đầu phân loại tạm của CNN được bỏ trước khi xây K-NN',64,612,1152,44,20);
}
// 6
{
  const s=page('Ảnh hưởng của k và khoảng cách','Nguồn: results/tuning/'+d.selected.feature+'.csv. Mỗi điểm là validation accuracy lớn nhất qua PCA và trọng số bỏ phiếu, ở k và metric tương ứng.');
  const colors=[green,'#556FA2','#B7832E'];
  chart(s,'line',{categories:d.sensitivity.categories,series:Object.entries(d.sensitivity.series).map(([name,values],i)=>({name,values,line:{fill:colors[i],width:3}})),hasLegend:true,
    xAxis:{title:'Số láng giềng k',textStyle:{fontSize:19,typeface:font}},
    yAxis:{min:.8,max:1,numberFormatCode:'0%',textStyle:{fontSize:18,typeface:font},majorGridlines:{fill:'#DCE6DF',width:1}}});
  text(s,`Cấu hình chọn: k = ${d.selected.k}, ${d.selected.metric}, ${d.selected.weights}, PCA = ${d.selected.pca || 'không dùng'}`,64,615,1152,42,18);
}
// 7
{
  const s=page('So sánh các nhánh K-NN','Nguồn: results/test_comparison.csv và results/validation_comparison.csv. Mô hình được chọn theo validation trước khi mở test.');
  const labels={'hsv_hog':'A','hsv_hog_segmented':'B','hsv_hog_hu_segmented':'B+Hu','resnet18':'C','efficientnet_b0':'D','resnet18_segmented':'C-mask','efficientnet_b0_segmented':'D-mask'};
  chart(s,'bar',{categories:d.comparison.map(r=>labels[r.feature]||'FT'),series:[{name:'Validation',values:d.comparison.map(r=>r.val_accuracy),fill:'#9DC7AE'},{name:'Test',values:d.comparison.map(r=>r.accuracy),fill:green}],hasLegend:true});
  text(s,'A: HSV+HOG   B: tách nền   C: ResNet18   D: EfficientNet-B0   FT: fine-tune',64,611,1152,45,17,false,muted);
}
// 8
{
  const s=page('Ma trận nhầm lẫn trên test','Nguồn: results/'+d.selected.feature+'_test_metrics.json. Hàng: nhãn thật. Cột: nhãn dự đoán. Mỗi hàng có 800 ảnh.');
  const values=[['Nhãn / đoán',...d.classes_vi],...d.test.confusion_matrix.map((row,i)=>[d.classes_vi[i],...row.map(String)])];
  const t=table(s,values,64,176,1152,420,18);
  for(let i=0;i<6;i++)t.getCell(i+1,i+1).fill='#C6E4D1';
  text(s,`Accuracy ${pct(d.test.accuracy)}   Macro-F1 ${d.test.macro_f1.toFixed(4)}   4.800 ảnh test`,64,615,1152,45,20,true);
}
// 9
{
  const s=page('Các trường hợp dự đoán sai','Nguồn: ảnh và sample IDs trong assets/deck_errors.json, dự đoán từ results/'+d.selected.feature+'_test_predictions.csv. Ảnh STL-10: '+stl);
  const errors=JSON.parse(await fs.readFile(path.join(root,'assets/deck_errors.json'),'utf8'));
  for(let i=0;i<Math.min(3,errors.length);i++){
    const e=errors[i],x=64+i*390;
    image(s,e.path,x,180,350,270,'Trường hợp dự đoán sai STL-10 '+e.sample_id);
    text(s,`Nhãn dữ liệu: ${e.truth_vi}`,x,477,350,45,20,true);
    text(s,`Dự đoán: ${e.pred_vi}`,x,522,350,45,20);
    text(s,`Điểm bỏ phiếu ${e.vote_score.toFixed(2)}`,x,567,350,42,17,false,muted);
  }
  text(s,'Giữ nguyên nhãn test; một số ảnh có dấu hiệu nhiễu nhãn hoặc ngoài sáu nhóm',64,629,1152,32,16,false,muted);
}
// 10
{
  const s=page('Kiểm tra 60 ảnh ngoài STL-10','Nguồn: data/external/manifest.csv và results/external_metrics.json. 10 ảnh Wikimedia mỗi nhóm, kiểm tra trực quan trước đánh giá. Giấy phép và tác giả: reports/EXTERNAL_ATTRIBUTION.html.');
  const names=['bird','cat','deer','dog','horse','monkey'];
  chart(s,'bar',{categories:d.classes_vi,series:[{name:'Tỷ lệ dự đoán đúng',values:names.map(n=>d.external.classification_report[n].recall),fill:green}],hasLegend:false});
  text(s,`Accuracy ${pct(d.external.accuracy)}   Macro-F1 ${d.external.macro_f1.toFixed(4)}   Trung vị ${d.external.median_ms.toFixed(0)} ms/ảnh`,64,611,1152,46,20);
}
// 11
{
  const s=page('Ứng dụng Windows','Nguồn: animal_knn/desktop.py; results/desktop_checks.json. K-NN chỉ dùng láng giềng từ train. Điểm bỏ phiếu không phải xác suất hiệu chuẩn. Tham khảo GUI: https://github.com/AlvaroVasquezAI/Animal_Image_Classification/blob/main/Program/main.py. Ảnh mẫu và giấy phép: assets/examples/sources.json. Chưa chụp được cửa sổ kết quả sau khi người dùng dừng điều khiển màn hình.');
  lines(s,['Chọn một ảnh JPG/PNG','Xem nhãn và điểm bỏ phiếu','Kiểm tra 5 ảnh train gần nhất'],64,190,360,23,128);
  image(s,'assets/examples/cat.jpg',540,165,370,310,'Ảnh mèo mẫu dùng kiểm tra ứng dụng');
  text(s,'Ảnh mẫu kiểm tra · Kết quả khớp backend',510,490,690,40,18);
  text(s,'Cửa sổ Tkinter/ttk · Xử lý ở luồng nền',510,535,690,40,18);
  text(s,'Nhấp đúp run-desktop.bat · Tkinter/ttk · Chạy từ mã nguồn',64,620,1152,40,19);
}
// 12
{
  const s=page('Giới hạn và hướng phát triển','Nguồn: báo cáo thực nghiệm reports/BAO_CAO.md. Đặc tả và giới hạn ghi rõ trong README. Dữ liệu: '+stl);
  lines(s,['Sáu nhóm đã biết, chưa phát hiện lớp lạ','Tiền huấn luyện ImageNet cần được công bố rõ','Một số ảnh có dấu hiệu nhiễu nhãn bộ dữ liệu','Bộ ngoài 60 ảnh nhỏ và có thiên lệch tuyển chọn','Mở rộng dữ liệu độc lập, nhiều seed và lớp chưa biết'],64,160,1152,22,94);
}

for(const [index,slide] of presentation.slides.items.entries()){
  const png=await presentation.export({slide,format:'png',scale:1});
  await fs.writeFile(path.join(build,`slide-${String(index+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
}
let revision=1;
let candidatePath;
do {candidatePath=path.join(build,`candidate-v${revision++}.pptx`);} while(await fs.stat(candidatePath).then(()=>true,()=>false));
await (await PresentationFile.exportPptx(presentation)).save(candidatePath);
const finalPath=path.join(root,'reports/THUYET_TRINH.pptx');
const result=await finalizePresentation({workspaceDir,candidatePath,finalPath,
  pythonExecutable:`${runtime}/python/python.exe`,
  integrityValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(SKILL_DIR,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide','4','--require-native-table-slide','8'],
  explicitTotalSlideCount:12,requiredNativeTableOwnerSlides:[4,8],requiredNativeChartOwnerSlides:[2,5,6,7,10],
  materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
  receiptPath:path.join(build,`validation-${path.basename(candidatePath,'.pptx')}.json`)});
console.log(JSON.stringify(result));
