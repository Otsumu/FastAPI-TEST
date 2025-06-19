//APIからデータを取得
async function loadMetricsData() {
    try {
        const response = await fetch('/api/metrics');
        const data  = await response.json();
        return data;
    } catch (error) {
        console.error('データ取得エラー:', error);
        return null;            
    }
}

// CPU使用率グラフ作成
function createCpuUsageChart(data) {
    //2次元描画モードのグラフを作成
    const context = document.getElementById('cpuLoadChart').getContext('2d');
    
    // CPU別にデータを作成する
    const cpuData = {};
    data.data.forEach(metric => {
        if (!cpuData[metric.cpu_name]) {
            cpuData[metric.cpu_name] = [];
        }
        cpuData[metric.cpu_name].push({
            x: metric.timestamp,
            y: metric.utilization
        });
    });
    
    // chart.jsのデータを作成
    const datasets = Object.keys(cpuData).map((cpuName, index) => {
        const colors = ['red','green','blue','yellow'];
        
        return {     
        label: cpuName,
        data: cpuData[cpuName],
        borderColor:  colors[index],
        tension: 0.4,
        fill: false //塗りつぶしなし
        };
    });
    //chart.jsに新しいグラフオブジェクトを作る
    new Chart(context, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            scales: {
                x: { 
                    type: 'time',
                    title: { display: true, text: '時間' }
                },
                y: { 
                    beginAtZero: true,
                    max: 100,
                    title: { display: true, text: 'CPU使用率(%)' }
                }
            }
        }
    });
}

// 関数の呼び出し
loadMetricsData().then(data => {
    if (data) {
        createCpuUsageChart(data);
    }
});

// 関数の呼び出し then()を使用しないコード
//(async () => {
//    const data = await loadMetricsData();
//    if (data) {
//        createCpuUsageChart(data);
//    }
//}) (); 