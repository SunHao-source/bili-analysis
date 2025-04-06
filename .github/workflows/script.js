async function runAnalysis() {
    const bvid = document.getElementById('bvid').value;
    if (!bvid) return alert('请输入BV号');
    
    document.getElementById('status').innerHTML = '正在生成...';
    
    // 调用GitHub Actions
    const response = await fetch(`https://api.github.com/repos/YOUR_USERNAME/bili-analysis/dispatches`, {
        method: 'POST',
        headers: {
            'Authorization': 'token YOUR_PAT',
            'Accept': 'application/vnd.github.everest-preview+json'
        },
        body: JSON.stringify({
            event_type: 'run_analysis',
            client_payload: { bvid: bvid }
        })
    });
    
    // 轮询检查结果
    const timer = setInterval(() => {
        checkResult(bvid).then(result => {
            if (result) {
                clearInterval(timer);
                document.getElementById('output-image').src = result;
                document.getElementById('output-image').style.display = 'block';
                document.getElementById('status').innerHTML = '分析完成';
            }
        });
    }, 5000);
}

async function checkResult(bvid) {
    // 检查结果文件是否生成
    const imageUrl = `https://raw.githubusercontent.com/YOUR_USERNAME/bili-analysis/main/output_${bvid}_heatmap.png`;
    const response = await fetch(imageUrl);
    return response.ok ? imageUrl : null;
}
