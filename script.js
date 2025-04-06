async function analyze() {
  const bvid = document.getElementById('bvid-input').value.trim();
  
  // 验证BVID格式
  if (!/^BV\w{10}$/.test(bvid)) {
    alert('请输入有效的BV号（如BV1GJ411x7h7）');
    return;
  }

  const btn = document.getElementById('analyze-btn');
  btn.disabled = true;
  btn.textContent = '分析中...';

  try {
    // 通过代理服务调用（避免暴露PAT）
    const response = await fetch('https://your-proxy-service.com/trigger', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bvid })
    });

    if (!response.ok) throw new Error('触发分析失败');

    // 轮询结果（带超时机制）
    await pollResults(bvid);
    
  } catch (error) {
    console.error('分析出错:', error);
    document.getElementById('result').innerHTML = `
      <p class="error">分析失败: ${error.message}</p>
    `;
  } finally {
    btn.disabled = false;
    btn.textContent = '开始分析';
  }
}

// 改进的轮询函数
async function pollResults(bvid, timeout = 300000, interval = 10000) {
  const startTime = Date.now();
  
  while (Date.now() - startTime < timeout) {
    try {
      // 添加时间戳避免缓存
      const result = await fetch(
        `https://your-username.github.io/your-repo/report_${bvid}.html?t=${Date.now()}`
      );
      
      if (result.ok) {
        document.getElementById('result').innerHTML = `
          <h3>分析完成！</h3>
          <a href="https://your-username.github.io/your-repo/output_${bvid}.json" download>下载数据文件</a>
          <a href="https://your-username.github.io/your-repo/report_${bvid}.html" download>查看完整报告</a>
        `;
        return;
      }
    } catch (error) {
      console.warn('轮询失败:', error);
    }
    
    await new Promise(resolve => setTimeout(resolve, interval));
  }
  
  throw new Error('获取结果超时，请稍后刷新页面查看');
}
