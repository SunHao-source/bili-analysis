async function analyze() {
  const bvid = document.getElementById('bvid-input').value;
  
  // BVID格式验证
  if(!/^BV\w{10}$/.test(bvid)) {
    alert('请输入有效的BVID（如BV1GJ411x7h7）');
    return;
  }

  try {
    // 通过代理服务调用GitHub API（避免暴露PAT）
    const response = await fetch('https://your-proxy-service.com/trigger-analysis', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ bvid })
    });

    if(!response.ok) throw new Error('触发分析失败');
    
    // 改进的轮询机制
    await pollResults(bvid);
    
  } catch(error) {
    console.error('分析出错:', error);
    document.getElementById('result').innerHTML = `
      <p class="error">分析失败: ${error.message}</p>
    `;
  }
}

// 带超时的轮询函数
async function pollResults(bvid, timeout=600000, interval=10000) {
  const startTime = Date.now();
  
  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      try {
        // 检查是否超时
        if(Date.now() - startTime > timeout) {
          clearInterval(timer);
          reject(new Error('分析超时'));
          return;
        }

        // 尝试获取结果
        const result = await fetch(`https://sunhao-source.github.io/bili-analysis/output_${bvid}.json?t=${Date.now()}`);
        
        if(result.ok) {
          clearInterval(timer);
          const data = await result.json();
          displayResult(data);
          resolve();
        }
      } catch(error) {
        clearInterval(timer);
        reject(error);
      }
    }, interval);
  });
}
