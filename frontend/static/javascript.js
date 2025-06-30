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

// 共通のデータ処理関数
function processCpuData(data) {
    const cpuData = {};
    Object.keys(data).forEach(cpuName => {
        cpuData[cpuName] = data[cpuName].map(point => ({
            x:point.timestamp,
            y:point.utilization
        }))
    })
    //10の倍数に切り上げてグラフの見た目を良くする
    const maxUsage = Math.max(...Object.values(cpuData).flat().map(data => data.y));
    const suggestedMax = Math.ceil(maxUsage / 10) * 10;
    
    return { cpuData, suggestedMax };
}
//cpuのグラフ色生成
function cpuColor(index) {
    const baseColors = ['#06B6D0', '#8B5CF3', '#F97312', '#DC2620', '#10B982', '#F59E0C', '#EF4445', '#8B5A2C'];
    const colorSteps = 16;

    if (index < baseColors.length) {
        return baseColors[index];
    } else {
        const hue = (index * 360 / colorSteps) % 360;
        return  `hsl(${hue}, 70%, 50%) `
    }
}

// CPU使用率グラフ(全体)作成
function createCpuUsageChart(data) {
    //2次元描画モードのグラフを作成
    const context = document.getElementById('cpuLoadChart').getContext('2d');
    //processCpuData()呼び出し
    const { cpuData, suggestedMax } = processCpuData(data);

    // chart.jsのデータを作成
    const datasets = Object.keys(cpuData).map((cpuName, index) => {
        return {     
            label: cpuName,
            data: cpuData[cpuName].filter((_, index) => index % 3 === 0),
            borderColor:  cpuColor(index),
            backgroundColor: cpuColor(index),
            tension: 0,
            fill: false, 
            pointRadius: 3,
            pointHoverRadius: 6
        };
    });

    //chart.jsに新しいグラフオブジェクトを作る(全体用)
    new Chart(context, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            scales: {
                x: { 
                    type: 'time',
                    stepSize: 30,
                    title: { display: true, text: '時刻' },
                    time: {
                        unit: 'minute',
                        displayFormats: {
                            minute: 'HH:mm'
                        }
                    },
                    ticks: {
                        maxTicksLimit: 6,
                        autoSkip: false
                    }
                },
                y: { 
                    beginAtZero: true,
                    max: suggestedMax,
                    ticks: {
                        stepSize: 10
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