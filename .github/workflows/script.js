async function analyze() {
  const bvid = document.getElementById('bvid-input').value;
  console.log('正在分析:', bvid);
  
  // 触发GitHub Actions
  const response = await fetch(`https://api.github.com/repos/SunHao-source/bili-analysis/actions/workflows/main.yml/dispatches`, {
    method: 'POST',
    headers: {
      'Authorization': 'token YOUR_PAT',
      'Accept': 'application/vnd.github.v3+json'
    },
    body: JSON.stringify({
      ref: 'main',
      inputs: { bvid: bvid }
    })
  });

  // 轮询结果（每10秒检查一次）
  const checkInterval = setInterval(async () => {
    const result = await fetch('https://sunhao-source.github.io/bili-analysis/output.json');
    if (result.ok) {
      clearInterval(checkInterval);
      displayResult(await result.json());
    }
  }, 10000);
}
window.analyze = analyze;
