"""Generate Vietnamese Markdown and standalone HTML from measured study outputs."""
from __future__ import annotations

import base64
import html
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from animal_knn.common import ROOT,CLASSES,VI,save_json


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def md_table(frame):
    return '| '+' | '.join(map(str,frame.columns))+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+'\n'.join('| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in frame.itertuples(index=False,name=None))


def main():
    root=ROOT
    reports=root/'reports'
    reports.mkdir(exist_ok=True)
    selected=read(root/'models/selection.json')['config']
    feature=selected['feature']
    measured=read(root/'results'/f'{feature}_test_metrics.json')
    external=read(root/'results/external_metrics.json')
    manifest=pd.read_csv(root/'data/processed/manifest.csv')
    validation=pd.read_csv(root/'results/validation_comparison.csv')
    tests=pd.read_csv(root/'results/test_comparison.csv')
    tuning=pd.read_csv(root/'results/tuning'/f'{feature}.csv')
    counts=manifest.groupby(['split','class_name']).size().unstack(fill_value=0).reindex(columns=CLASSES)
    counts=counts.reindex([s for s in ['train','val','test','excluded_near_duplicate','excluded_duplicate'] if s in counts.index])
    counts.columns=VI
    counts=counts.reset_index().rename(columns={'split':'Tập dữ liệu'})
    curve=tuning.groupby(['k','metric']).val_accuracy.max().unstack()
    fig,ax=plt.subplots(figsize=(8,4.6))
    for name in curve.columns:
        ax.plot(curve.index,curve[name]*100,marker='o',label=name)
    ax.set(xlabel='Số láng giềng k',ylabel='Validation accuracy (%)',title='Ảnh hưởng của k và khoảng cách')
    ax.legend();ax.grid(alpha=.2);fig.tight_layout();fig.savefig(root/'results/knn_sensitivity.png',dpi=150);plt.close(fig)
    joined=tests.merge(validation[['feature','val_accuracy']],on='feature')
    fig,ax=plt.subplots(figsize=(11,5.4))
    names=joined.feature.tolist();x=np.arange(len(names));w=.36
    ax.bar(x-w/2,joined.val_accuracy*100,w,label='Validation',color='#80ad95')
    ax.bar(x+w/2,joined.accuracy*100,w,label='Test',color='#176b45')
    ax.set(ylim=(0,100),ylabel='Accuracy (%)',xticks=x,xticklabels=names,title='So sánh các nhánh K-NN')
    ax.tick_params(axis='x',rotation=30,labelsize=8);ax.legend();fig.tight_layout();fig.savefig(root/'results/model_comparison.png',dpi=150);plt.close(fig)

    blocks=[]
    def heading(text,level=2):blocks.append(('heading',text,level))
    def p(text):blocks.append(('p',text))
    def table(frame):blocks.append(('table',frame))
    def image(path,caption):blocks.append(('image',path,caption))
    def bullets(items):blocks.append(('ul',items))

    heading('Phân loại ảnh động vật bằng K-NN kết hợp đặc trưng màu sắc, hình dạng và học sâu',1)
    p('Báo cáo thực nghiệm · 18/11/2026 · Python, OpenCV, scikit-learn và PyTorch · sáu nhóm động vật STL-10')
    heading('1. Kết quả chính')
    p(f"Cấu hình được chọn bằng validation là {feature}, PCA={int(selected['pca']) or 'không dùng'}, k={int(selected['k'])}, khoảng cách {selected['metric']}, bỏ phiếu {selected['weights']}. Trên {measured['n_test']:,} ảnh test, accuracy đạt {measured['accuracy']:.2%} và macro-F1 đạt {measured['macro_f1']:.4f}. Khoảng tin cậy 95% xấp xỉ của accuracy là {measured['accuracy_normal_95ci'][0]:.2%}–{measured['accuracy_normal_95ci'][1]:.2%} theo giả định các mẫu độc lập.")
    target=measured['accuracy']>=.9 and measured['macro_f1']>=.9
    p('Mục tiêu accuracy và macro-F1 từ 0,90 '+('đã đạt trong thiết lập đánh giá này.' if target else 'chưa đạt trong thiết lập đánh giá này. Số liệu được giữ nguyên để phản ánh đúng kết quả.'))
    p(f"Bộ ngoài gồm 60 ảnh Wikimedia có accuracy {external['accuracy']:.2%}, macro-F1 {external['macro_f1']:.4f}. Thời gian suy luận sau warm-up có trung vị {external['median_ms']:.1f} ms và phân vị 95 là {external['p95_ms']:.1f} ms trên máy triển khai, không gồm khởi tạo mô hình và giải mã tệp ảnh. Đây là kiểm tra bổ sung nhỏ, có thiên lệch tuyển chọn.")

    heading('2. Bài toán và tài liệu liên quan')
    p('Đầu vào là một ảnh có động vật nổi bật. Đầu ra thuộc một trong sáu nhóm: chim, mèo, hươu, chó, ngựa, khỉ. Đây là nhóm nhãn của bộ dữ liệu, không phải hệ phân loại loài sinh học chi tiết. K-NN là bộ phân loại cuối trong tất cả các nhánh; CNN chỉ tạo vector biểu diễn.')
    table(pd.DataFrame([
        ['Animal Image Classification','So sánh histogram, kết cấu và VGG16 với K-NN/SVM.','https://github.com/elfchildRichter/Animal_Image_Classification_Unsupervised'],
        ['Coarse-to-Fine Image Classification','HOG, màu sắc và embedding ResNet18 cho nhóm động vật.','https://github.com/paigenewin/coarse-to-fine-image-classification'],
        ['ResNet18 STL-10 Transfer Learning','Fine-tune, phát hiện quá khớp và phân tích từng lớp.','https://github.com/reluv17/resnet18-stl10-transfer-learning']
    ],columns=['Dự án','Ý nghĩa tham khảo','Nguồn']))
    p('Các kho tham khảo giúp định hướng phương pháp. Báo cáo chỉ sử dụng số liệu do dự án này chạy được; không sao chép kết quả công bố của các kho trên.')

    heading('3. Dữ liệu, làm sạch và giao thức')
    p('STL-10 cung cấp ảnh RGB 96 × 96. Dùng 3.000 ảnh có nhãn thuộc sáu nhóm trong train gốc và 4.800 ảnh thuộc sáu nhóm trong test gốc. Chia 80/20 train/validation có phân tầng theo lớp, seed 42. Bốn tệp nhị phân tải trực tiếp từ Stanford khớp MD5 trong Torchvision; không sử dụng tập 100.000 ảnh không nhãn.')
    p('Phát hiện ứng viên gần trùng bằng perceptual hash DCT 63 bit, ngưỡng Hamming không quá 5. Kiểm tra trực quan xác nhận 21 quan hệ gần trùng, tương ứng 20 ảnh cần loại: 15 train và 5 validation. Giữ ưu tiên test rồi validation rồi train. Những ảnh này là cùng bức ảnh có thay đổi nén/kích thước. Sau làm sạch, kiểm tra chéo không còn ứng viên trong ngưỡng đã chọn. Kết quả kiểm tra không phải bảo đảm rằng mọi kiểu trùng ngữ nghĩa đã được phát hiện.')
    table(counts)
    p('Danh sách ảnh, SHA-256, nhãn, tập dữ liệu và quyết định loại ảnh được lưu để tái lập. Không có mẫu validation/test trong tập tham chiếu K-NN. Không có trùng ảnh chính xác theo SHA-256 giữa các tập ban đầu.')
    p('STL-10 lấy ảnh từ ImageNet, trong khi ResNet18 và EfficientNet-B0 sử dụng trọng số ImageNet-1K. Vì vậy, đây là đánh giá transfer learning trên tập con sáu lớp. Không so sánh trực tiếp với giao thức STL-10 10-fold chính thức hoặc mô hình chỉ học từ STL-10. Nghiên cứu chưa kiểm chứng việc trùng ảnh với toàn bộ dữ liệu tiền huấn luyện ImageNet.')

    heading('4. Tiền xử lý và trích đặc trưng')
    p('Ảnh được sửa hướng EXIF, chuyển RGB, ghép nền trắng cho ảnh có alpha và đưa về 96 × 96. Nhánh CNN tiếp tục dùng phép biến đổi suy luận đi kèm trọng số Torchvision. Tất cả mẫu train, validation, test và ảnh người dùng đi qua cùng quy trình.')
    table(pd.DataFrame([
        ['HSV','Histogram 8 × 8 × 8, chuẩn hóa tổng bằng 1','512'],
        ['HOG','9 hướng, cell 8 × 8, block 2 × 2, L2-Hys','4.356'],
        ['Hu moments','7 moments sau biến đổi log, từ mặt nạ','7'],
        ['ResNet18','Vector sau pooling, bỏ lớp fully connected','512'],
        ['EfficientNet-B0','Vector sau pooling, bỏ classifier','1.280']
    ],columns=['Đặc trưng','Thiết lập','Số chiều']))
    p('GrabCut khởi tạo hình chữ nhật (3,3,90,90), chạy 5 vòng; mở và đóng hình thái với kernel 3 × 3. Nếu tỷ lệ foreground ngoài [0,05; 0,95] hoặc OpenCV báo lỗi, quay về ảnh gốc và ghi nhận fallback. Màu nền sau tách đối tượng là RGB (127,127,127). Hu moments được đặt 0 khi fallback. Không chỉnh mask theo nhãn hoặc bằng tay cho từng ảnh test.')
    segment_meta=root/'data/processed/segmentation.json'
    if segment_meta.exists():
        meta=read(segment_meta)
        p(f"Trong {meta['samples']:,} ảnh đã tiền xử lý, GrabCut fallback {meta['fallbacks']:,} lần. Không có mặt nạ ground truth cho tập nghiên cứu nên không báo cáo IoU; ảnh hưởng của phân đoạn được đo qua phân loại với cùng bộ đặc trưng.")
    image(root/'results/segmentation_examples.png','Ví dụ ảnh gốc, mặt nạ tự động và ảnh sau tách nền từ train.')

    heading('5. Khảo sát K-NN và fine-tune')
    p('K-NN được khảo sát với k ∈ {1,3,5,7,11,15}, khoảng cách Euclidean/Manhattan/cosine, bỏ phiếu uniform/distance và PCA không dùng/128/256 chiều: 108 cấu hình cho mỗi bộ đặc trưng. Scaler của nhánh thủ công và PCA chỉ fit train. Chuẩn hóa L2 được áp dụng trước K-NN. Các khoảng cách và láng giềng được tái sử dụng trong khảo sát để giảm tính toán, còn mô hình bàn giao dùng KNeighborsClassifier của scikit-learn.')
    p('Chọn cấu hình theo validation accuracy, rồi macro-F1, rồi thời gian tìm láng giềng khi hòa điểm. Chỉ tính chỉ số phân loại trên test sau khi đã lưu lựa chọn cuối và dấu vết SHA-256. Kiểm tra dữ liệu và tiền xử lý ảnh không học từ nhãn test. Các lệnh tune, fine-tune và select từ chối thay đổi nghiên cứu sau khi đánh giá test.')
    history_path=root/'results/finetune_history.json'
    if history_path.exists():
        history=read(history_path)
        p(f"Backbone được fine-tune là {history['backbone']}. Huấn luyện đầu tạm 5 epoch với AdamW lr=0,001; sau đó mở khối cuối tối đa 10 epoch, lr=0,0001 cho cả đầu và khối cuối, weight decay=0,0001. Batch 16, mixed precision trên GPU. Dừng sớm khi validation loss không cải thiện trong 3 epoch. Các khối đóng băng giữ chế độ eval để thống kê BatchNorm không trôi. Đã chạy tổng cộng {len(history['history'])} epoch; checkpoint có validation loss thấp nhất được giữ, bỏ đầu phân loại rồi trích lại vector cho K-NN.")
    image(root/'results/knn_sensitivity.png','Accuracy tốt nhất trên validation theo k và khoảng cách, lấy tối đa qua các cấu hình PCA/bỏ phiếu.')

    heading('6. Kết quả so sánh')
    display=joined[['feature','val_accuracy','accuracy','macro_f1','selected_on_validation']].copy()
    display.columns=['Đặc trưng','Validation accuracy','Test accuracy','Test macro-F1','Được chọn bằng validation']
    for name in ['Validation accuracy','Test accuracy']:
        display[name]=display[name].map(lambda v:f'{v:.2%}')
    display['Test macro-F1']=display['Test macro-F1'].map(lambda v:f'{v:.4f}')
    table(display)
    p('Mỗi nhánh trong bảng đã chọn tham số bằng validation trước khi đánh giá test. Điểm test của các nhánh là thông tin mô tả sau khóa nghiên cứu, không được dùng để đổi mô hình đã chọn.')
    image(root/'results/model_comparison.png','So sánh các bộ đặc trưng với cùng bộ phân loại cuối K-NN.')
    baseline=tests[tests.feature=='hsv_hog'].iloc[0]
    p(f"So với HSV+HOG trên ảnh gốc, mô hình được chọn có chênh lệch test accuracy {(measured['accuracy']-baseline.accuracy)*100:+.2f} điểm phần trăm. Khác biệt này phản ánh cả biểu diễn đặc trưng và cấu hình K-NN được chọn tương ứng, không phải kiểm định nhân quả độc lập cho từng thành phần.")
    seg=tests[tests.feature=='hsv_hog_segmented']
    if len(seg):
        difference=(float(seg.iloc[0].accuracy)-float(baseline.accuracy))*100
        p(f"Với cùng HSV+HOG, tách nền làm thay đổi test accuracy {difference:+.2f} điểm phần trăm. Tác dụng phân đoạn không được giả định trước là luôn có lợi; kết quả phụ thuộc việc giữ đúng đối tượng và mất hay giữ thông tin ngữ cảnh.")

    heading('7. Phân tích từng lớp và lỗi')
    per_class=[]
    for name,vi in zip(CLASSES,VI):
        row=measured['classification_report'][name]
        per_class.append([vi,f"{row['precision']:.4f}",f"{row['recall']:.4f}",f"{row['f1-score']:.4f}",int(row['support'])])
    table(pd.DataFrame(per_class,columns=['Nhóm','Precision','Recall','F1','Số ảnh']))
    image(root/'results'/f'{feature}_confusion.png','Ma trận nhầm lẫn của mô hình đã chọn. Số trong ô là số ảnh, màu thể hiện tỷ lệ theo lớp thật.')
    cm=np.array(measured['confusion_matrix'])
    p(f"Chó bị dự đoán thành mèo {cm[3,1]} lần, mèo thành chó {cm[1,3]} lần. Hươu thành ngựa {cm[2,4]} lần, ngựa thành hươu {cm[4,2]} lần. Các lỗi cần xem theo dáng, tư thế, tỉ lệ đối tượng và nền thay vì chỉ dựa vào nhãn tổng hợp.")
    image(root/'results/error_gallery.png','Ví dụ dự đoán sai trên test, ưu tiên các lỗi có điểm bỏ phiếu cao trong từng lớp. Điểm cao vẫn có thể sai.')
    p('Các phép đo so sánh dự đoán với nhãn công bố của bộ dữ liệu. Quan sát trực quan một số ảnh sai có điểm cao cho thấy dấu hiệu nhiễu nhãn hoặc động vật ngoài sáu nhóm. Đã đối chiếu chỉ số ảnh, pixel và nhãn với tệp nhị phân gốc để loại trừ lỗi ghép ảnh/nhãn của chương trình. Không sửa nhãn test sau khi xem kết quả; các trường hợp này được giữ lại và nêu như một giới hạn của đánh giá.')

    heading('8. Đánh giá ngoài STL-10')
    p('Bộ cố định gồm 60 ảnh Wikimedia Commons, 10 ảnh mỗi nhóm, thu thập trước khi xem kết quả mô hình. Kiểm tra trực quan loại ảnh trứng, bộ xương và áo lông không phù hợp. Mỗi ảnh giữ tên tệp, trang nguồn, tác giả, giấy phép, ngày nguồn cung cấp và SHA-256. Không phát hiện ứng viên gần trùng với STL-10 ở ngưỡng perceptual hash đã dùng.')
    ext_rows=[]
    for name,vi in zip(CLASSES,VI):
        r=external['classification_report'][name]
        ext_rows.append([vi,int(r['support']),f"{r['recall']:.2%}",f"{r['f1-score']:.4f}"])
    table(pd.DataFrame(ext_rows,columns=['Nhóm','Số ảnh','Tỷ lệ dự đoán đúng','F1']))
    image(root/'results/external_confusion.png','Ma trận nhầm lẫn trên 60 ảnh Wikimedia. Bộ này không tham gia chọn tham số.')
    p('Giới hạn: cỡ mẫu nhỏ, nhiều ảnh chụp rõ đối tượng và truy vấn thiên về một số giống/loài. Một số ảnh có tuổi đời trước ImageNet và có thể xuất hiện trong nguồn tiền huấn luyện; nghiên cứu không tuyên bố bộ này hoàn toàn chưa từng được backbone nhìn thấy. Không suy rộng accuracy này cho mọi ảnh Internet.')

    heading('9. Demo và kiểm chứng phần mềm')
    p('Ứng dụng Windows viết bằng Tkinter/ttk, mở từ mã nguồn qua run-desktop.bat. Cửa sổ nhận JPG/PNG qua hộp chọn tệp Windows, hiển thị nhãn, điểm bỏ phiếu, thời gian, ảnh tiền xử lý và năm láng giềng chỉ từ train. Nạp mô hình và suy luận chạy ở luồng nền, cập nhật widget ở luồng chính. Bộ mô hình gồm encoder, chuẩn hóa/PCA, K-NN, nhãn và ảnh tham chiếu nên không cần trình duyệt, web server hoặc Internet khi phân loại.')
    checks=root/'results/verification.json'
    if checks.exists():
        verification=read(checks)
        labels={'official_binary_md5':'Checksum dữ liệu gốc',
            'reference_count_train_only':'Số ảnh tham chiếu, chỉ từ train',
            'no_exact_hash_overlap':'Không trùng SHA-256 giữa train và holdout',
            'curated_near_duplicate_candidates':'Ứng viên gần trùng còn lại sau làm sạch',
            'cached_online_features_consistent':'Vector cache và suy luận trực tiếp tương thích',
            'cached_online_votes_consistent':'Điểm bỏ phiếu cache và trực tiếp nhất quán',
            'cached_online_max_relative_l2':'Sai khác L2 tương đối lớn nhất giữa các batch',
            'stored_validation_metrics_reproduced':'Tái lập đúng chỉ số validation của mô hình đã lưu',
            'reproduced_validation_accuracy':'Validation accuracy tái lập',
            'cpu_gpu_prediction_consistency_samples':'Số mẫu cùng dự đoán trên CPU và GPU',
            'serialization_roundtrip':'Giữ nguyên dự đoán sau lưu/nạp mô hình',
            'unit_tests':'Kiểm thử tự động','selected_feature':'Đặc trưng được chọn','demo_expected_label_vi':'Kết quả ảnh demo'}
        values=[]
        for key,value in verification.items():
            display='Đạt' if value is True else 'Không đạt' if value is False else str(value)
            if key=='cached_online_max_relative_l2': display=f'{value:.4%}'
            if key=='reproduced_validation_accuracy': display=f'{value:.2%}'
            if key=='unit_tests' and value=='11 passed': display='11 kiểm tra thành công'
            values.append([labels.get(key,key),display])
        table(pd.DataFrame(values,columns=['Kiểm tra','Kết quả']))
    desktop_path=root/'results/desktop_checks.json'
    if desktop_path.exists():
        desktop=read(desktop_path)
        p('Kiểm tra giao diện Windows: '+desktop['summary'])
    screenshot=root/'reports/demo_desktop.png'
    if screenshot.exists():
        image(screenshot,'Cửa sổ ứng dụng Windows với dữ liệu và kết quả thật.')

    heading('10. Giới hạn và hướng phát triển')
    bullets(['Chỉ chọn trong sáu nhóm đã biết, chưa phát hiện lớp lạ hoặc ảnh không chứa động vật.',
        'Ảnh nhiều đối tượng, che khuất, ánh sáng khó và thay đổi miền dữ liệu có thể làm giảm độ chính xác.',
        'Phân đoạn GrabCut có thể làm mất bộ phận quan trọng; chưa có đo IoU bằng ground truth.',
        'Một số ảnh minh họa có dấu hiệu nhiễu nhãn bộ dữ liệu; chỉ số test vẫn dùng nhãn công bố, chưa hiệu đính.',
        'Chưa loại hết khả năng trùng nguồn với ImageNet tiền huấn luyện, vì vậy phải giữ mô tả transfer learning.',
        'Thí nghiệm fine-tune dùng một seed chính; chưa đo độ biến thiên qua nhiều lần huấn luyện độc lập.',
        'Bước tiếp theo: bộ ảnh ngoài lớn và đa dạng hơn, kiểm chứng nguồn tiền huấn luyện, bổ sung nhận biết lớp lạ và nhiều seed.'])
    heading('11. Tái lập và nguồn')
    p('README mô tả môi trường, từng lệnh CLI và cách tái lập trong thư mục mới. requirements.lock.txt khóa phiên bản. data/curation ghi quyết định làm sạch; results/tuning chứa toàn bộ grid; models/selection.json và results/test_access_receipt.json ghi lựa chọn trước test. Agent Reach 1.6.1 được cài trong môi trường dự án và đã kiểm tra tìm kiếm/đọc web.')
    sources=[('STL-10, Stanford','https://cs.stanford.edu/~acoates/stl10/'),
        ('Torchvision STL-10 source','https://github.com/pytorch/vision/blob/v0.24.1/torchvision/datasets/stl10.py'),
        ('PyTorch transfer learning','https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html'),
        ('KNeighborsClassifier','https://scikit-learn.org/stable/modules/generated/sklearn.neighbors.KNeighborsClassifier.html'),
        ('OpenCV GrabCut','https://docs.opencv.org/4.x/d8/d83/tutorial_py_grabcut.html'),
        ('Agent Reach','https://github.com/Panniantong/Agent-Reach'),
        ('Tkinter, Python 3.10','https://docs.python.org/3.10/library/tkinter.html'),
        ('HOG/SIFT/ORB và K-NN cho động vật','https://github.com/RANA-ATI/Animals-Classification-using-Feature-Extractors'),
        ('Đặc trưng HSV/VGG16 và K-NN','https://github.com/elfchildRichter/Animal_Image_Classification_Unsupervised'),
        ('GUI Tkinter phân loại động vật','https://github.com/AlvaroVasquezAI/Animal_Image_Classification'),
        ('Animal classifier GUI','https://github.com/cyproto/image_classification-animals-with-gui')]
    bullets([name+': '+url for name,url in sources])
    p('Nguồn và giấy phép từng ảnh ngoài nằm trong data/external/manifest.csv và reports/EXTERNAL_ATTRIBUTION.html. Mã dự án có giấy phép MIT; dữ liệu và trọng số giữ điều khoản nguồn gốc.')
    p('Các kho cùng hướng được đối chiếu về nhánh đặc trưng và luồng GUI, không dùng số liệu công bố của họ làm kết quả. Nội dung đã đọc và quyết định áp dụng được ghi trong reports/DU_AN_THAM_KHAO.md; mã cửa sổ của đồ án được viết riêng.')

    md=[];body=[]
    for block in blocks:
        kind=block[0]
        if kind=='heading':
            _,text,level=block;md.append('#'*level+' '+text);body.append(f'<h{level}>{html.escape(text)}</h{level}>')
        elif kind=='p':
            md.append(block[1]);body.append('<p>'+html.escape(block[1])+'</p>')
        elif kind=='ul':
            md.append('\n'.join('- '+s for s in block[1]));body.append('<ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in block[1])+'</ul>')
        elif kind=='table':
            md.append(md_table(block[1]));body.append(block[1].to_html(index=False,escape=True,border=0))
        elif kind=='image':
            path,caption=block[1:]
            if not path.exists():continue
            relative=Path('..')/path.relative_to(root)
            md.append(f'![{caption}]({relative.as_posix()})')
            encoded=base64.b64encode(path.read_bytes()).decode()
            body.append(f'<figure><img src="data:image/png;base64,{encoded}" alt="{html.escape(caption)}"><figcaption>{html.escape(caption)}</figcaption></figure>')
    (reports/'BAO_CAO.md').write_text('\n\n'.join(md)+'\n',encoding='utf-8')
    css='''body{font:16px/1.65 "Segoe UI",Arial,sans-serif;color:#18352a;max-width:1020px;margin:48px auto;padding:0 28px}h1{font-size:34px;line-height:1.2;max-width:900px}h2{margin:42px 0 14px;font-size:24px}p{margin:14px 0}table{border-collapse:collapse;width:100%;font-size:13px;margin:20px 0;overflow-wrap:anywhere}th{background:#e5efe9;text-align:left}td,th{padding:10px;border-bottom:1px solid #cad9cf}figure{margin:26px 0;break-inside:avoid}img{max-width:100%;height:auto}figcaption{font-size:13px;color:#486555;margin-top:8px}li{margin:8px 0}@media print{body{margin:0;max-width:none;padding:0;font-size:11pt}h1{font-size:24pt}h2{font-size:17pt;break-after:avoid}thead{display:table-header-group}tr{break-inside:avoid}table{font-size:9pt}figure{max-height:240mm}img{max-height:205mm;object-fit:contain}a{color:inherit}@page{size:A4;margin:18mm}}'''
    (reports/'BAO_CAO.html').write_text('<!doctype html><html lang="vi"><meta charset="utf-8"><title>Báo cáo Animal K-NN</title><style>'+css+'</style><body>'+''.join(body)+'</body></html>',encoding='utf-8')
    attribution=pd.read_csv(root/'data/external/manifest.csv')[['filename','title','source_page','author','license','license_url','date_original','visual_review']]
    (reports/'EXTERNAL_ATTRIBUTION.html').write_text('<!doctype html><html lang="vi"><meta charset="utf-8"><title>Nguồn ảnh Wikimedia</title><style>'+css+'</style><h1>Nguồn và giấy phép 60 ảnh ngoài</h1>'+attribution.to_html(index=False,escape=True,border=0,render_links=True)+'</html>',encoding='utf-8')
    save_json(reports/'deck_data.json',{'selected':selected,'test':measured,'external':external,
        'comparison':joined.to_dict(orient='records'),'counts':counts.to_dict(orient='records'),
        'sensitivity':{'categories':[str(k) for k in curve.index], 'series':{c:curve[c].tolist() for c in curve.columns}},
        'classes_vi':VI,'sources':[{'title':n,'url':u} for n,u in sources],
        'photo_sources':pd.read_csv(root/'data/external/manifest.csv')[['filename','source_page','author','license','license_url']].fillna('').set_index('filename').to_dict(orient='index')})
    print('Generated BAO_CAO.md, BAO_CAO.html, attribution and deck data',flush=True)


if __name__=='__main__':main()
