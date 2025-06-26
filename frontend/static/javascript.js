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
    data.data.forEach(metric => {
        if (!cpuData[metric.cpu_name]) {
            cpuData[metric.cpu_name] = [];
        }
        cpuData[metric.cpu_name].push({
            x: metric.timestamp,
            y: metric.utilization
        });
    });

    //10の倍数に切り上げてグラフの見た目を良くする
    const maxUsage = Math.max(...Object.values(cpuData).flat().map(data => data.y));
    const suggestedMax = Math.ceil(maxUsage / 10) * 10;
    
    return { cpuData, suggestedMax };
}

// CPU使用率グラフ(全体)作成
function createCpuUsageChart(data) {
    //2次元描画モードのグラフを作成
    const context = document.getElementById('cpuLoadChart').getContext('2d');
    //processCpuData()呼び出し
    const { cpuData, suggestedMax } = processCpuData(data);

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
    //chart.jsに新しいグラフオブジェクトを作る(全体用)
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
                    suggestedMax: suggestedMax,
                    ticks: {
                        stepSize: 6
                    },
                    title: { display: true, text: 'CPU使用率(%)' }
                }
            }
        }
    });
}

// CPU使用率グラフ(使用率が20%以下のデータのみ)作成
function createZoomedChart(data) {
    const zoomContext = document.getElementById('cpuLoadChartZoom').getContext('2d');
    const { cpuData } = processCpuData(data);

    // 20%以下のデータポイントのみ抽出
    const filteredCpuData = {};
    // 各CPUのデータをフィルタリング
    Object.keys(cpuData).forEach(cpuName => {
        filteredCpuData[cpuName] = cpuData[cpuName].filter(point => point.y <= 20);
    });
    
    // フィルタリング後のデータから最大値を再計算
    const filteredMaxUsage = Math.max(...Object.values(filteredCpuData).flat().map(data => data.y)
    );
    
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

    new Chart(zoomContext, {
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
                    min: 0,
                    max: filteredMaxUsage + 1.25,
                    suggestedMax: 20, // 20%以下のデータのみを表示する
                    ticks: {
                        stepSize: 1 // より細かい刻み
                    },
                    title: { display: true, text: '20%以下のみのCPU使用率(%) ' }
                }
            }
        }
    });
}


// 関数の呼び出し
loadMetricsData().then(data => {
    if (data) {
        createCpuUsageChart(data);
        createZoomedChart(data);
    }
});

// then()を使用しないコード、ページが開かれた時に、APIからデータを取得してグラフを描画する
//(async () => {
//    const data = await loadMetricsData();
//    if (data) {
//        createCpuUsageChart(data);
//        createZoomedChart(data);
//    }
//}) (); 