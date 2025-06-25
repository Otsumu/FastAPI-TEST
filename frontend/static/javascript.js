//APIからデータを取得
async function loadMetricsData() {
    try {
        const response = await fetch('/api/metrics');
        const data  = await response.json();
        console.log(data);
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
    
    const maxUsage = Math.max(...Object.values(cpuData).flat().map(d => d.y));
    const suggestedMax = Math.ceil(maxUsage / 10) * 10

    // chart.jsのデータを作成
    const datasets = Object.keys(cpuData).map((cpuName, index) => {
        const colors = [ '#06B6D4', '#8B5CF6', '#F97316', '#DC2626'];
    
        return {     
        label: cpuName,
        data: cpuData[cpuName],
        borderColor:  colors[index],
        backgroundColor: colors[index],
        tension: 0.5,
        fill: false, 
        pointRadius: 0,
        pointHoverRadius: 0
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
                    title: { display: true, text: '時刻' },
                    time: {
                        unit: 'second',
                        displayFormats: {
                            second: 'HH:mm:ss'
                        }
                    },
                    ticks: {
                        maxTicksLimit: 6,
                        autoSkip: true
                    }
                },
                y: { 
                    suggestedMin: 0,
                    suggestedMax: suggestedMax + 10,
                    ticks: {
                        stepSize: 3
                    },
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

// then()を使用しないコード、ページが開かれた時に、APIからデータを取得してグラフを描画する
//(async () => {
//    const data = await loadMetricsData();
//    if (data) {
//        createCpuUsageChart(data);
//    }
//}) (); 