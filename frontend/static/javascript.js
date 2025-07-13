//APIからデータを取得
async function loadMetricsData(mode ="realtime") {
    try {
        const response = await fetch(`/api/metrics?mode=${mode}`);
        const data  = await response.json();
        return data;
    } catch (error) {
        console.error('データ取得エラー:', error);
        return null;            
    }
}
// 時間間隔モード変更時の処理＆そのグラフの生成
async function modeChange(mode) {
    try {        
        if (mode === "realtime") {
            const data = await loadMetricsData(mode);
            createCpuUsageChart(data, mode);
        } else  {
            const data = await loadSummaryData(mode);
            createCpuUsageChart(data, mode);
        } 
    } catch (error) {
        console.error('モード変更エラー:', error);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // 初期データ読み込み
    loadMetricsData().then(data => {
        if (data) {
            createCpuUsageChart(data, 'realtime');
        }
    });
    
    const modeSelect = document.getElementById('modeSelect');
    if (modeSelect) {
        modeSelect.addEventListener('change', function() {
            const selectedMode = this.value;
            modeChange(selectedMode);
        });
    }
});

//生データ専用の処理関数
function processCpuData(data, mode) {
    const cpuData = {};
    Object.keys(data).forEach(cpuName => {
        cpuData[cpuName] = data[cpuName].map(point => ({
            x : mode === "realtime" ? new Date(point.timestamp * 1000) : point.timestamp,
            y : point.utilization 
        }))
    })
    //10の倍数に切り上げてグラフの見た目を良くする
    const maxUsage = Math.max(...Object.values(cpuData).flat().map(data => data.y));
    const suggestedMax = Math.ceil(maxUsage / 10) * 10;

    return { cpuData, suggestedMax };
}

//集計データを取得する関数定義
async function loadSummaryData(mode) {
    try {
        const timeRange = calculateTimeRange(mode);
        const response = await fetch(`/api/summary?start_timestamp=${timeRange.start}&end_timestamp=${timeRange.end}`);
        const data = await response.json()
        return data;
    }
    catch (error) {
        console.error('データ取得エラー:', error);
        return null;  
    }
}
//calculateTimeRange() → {start: 時刻, end: 時刻}オブジェクトを返す
function calculateTimeRange(mode) {
    const now = Math.floor(Date.now() / 1000); //1ミリ秒 = 1/1000秒、時刻は小数点以下切り捨て！
    let duration = 0;     //duration＝間隔、期間
    if (mode === "30minutes") {
        duration = 1800;
    } else if (mode === "1hour") { 
        duration = 3600;
    } else if (mode ==="1day") {
        duration = 86400;
    }
    return {
        start: now - duration,
        end:  now
    };
}

// CPU使用率グラフ(全体)作成 - modeパラメータを追加
function createCpuUsageChart(data, mode = 'realtime') {
    //2次元描画モードのグラフを作成
    const context = document.getElementById('cpuLoadChart').getContext('2d');
    //processCpuData()呼び出し
    if (mode === "realtime") {
        const { cpuData, suggestedMax } = processCpuData(data, mode);
    } else {
        const { cpuData, suggestedMax } = processSummaryData(data, mode);
    }   
    const timeSettings = getTimeSettings(mode);
    
    // chart.jsのデータを作成
    const datasets = Object.keys(cpuData).map((cpuName, index) => {
        const chartData = mode === "realtime" ? cpuData[cpuName].filter((_, index) => index % 3 === 0) : cpuData[cpuName];
        return {     
            label: cpuName,
            data: chartData,
            borderColor: cpuColor(index),
            backgroundColor: cpuColor(index),
            tension: 0,
            fill: false, 
            pointRadius: 3,
            pointHoverRadius: 6
        };
    });

    // 既存のチャートがあれば破棄
    if (cpuChart) {
        cpuChart.destroy();
    }

    // 新しいチャートを作成
    cpuChart = new Chart(context, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    labels: {
                        font: {
                            size: 16
                        }
                    }
                }
            },
            scales: {
                x: { 
                    type: 'time',
                    stepSize: timeSettings.stepSize,
                    title: { 
                        display: true, 
                        text: timeSettings.title,
                        font: {
                            size: 15
                        }       
                    },
                    time: {
                        unit: timeSettings.unit,
                        displayFormats: {
                            [timeSettings.unit]: timeSettings.displayFormat
                        }
                    },
                    ticks: {
                        maxTicksLimit: timeSettings.maxTicksLimit,
                        autoSkip: true,
                        padding: 10,
                        font: {
                            size: 15
                        }   
                    }
                },
                y: { 
                    beginAtZero: true,
                    max: suggestedMax,
                    ticks: {
                        stepSize: 10,
                        padding: 10,
                        font: {
                            size: 15
                        }                           
                    },
                    title: { 
                        display: true, 
                        text: 'CPU使用率(%)',
                        font: {
                            size: 15
                        }
                    },
                }
            }
        }    
    });
}

//集計処理専用の処理関数
function processSummaryData(data, mode) {
    try {
        console.log("集計データの例:", data.slice(0, 3));  // 最初の3件確認
        console.log("avg_utilization の値:", data.map(d => d.avg_utilization));

        const cpuData = {};
        data.forEach(item => {
        const cpuKey = `cpu${item.cpu_id}`;
        if(!cpuData[cpuKey]) cpuData[cpuKey] = [];
            cpuData[cpuKey].push({
            x : new Date(item.bucket_timestamp * 1000),
            y : item.avg_utilization 
        });
    })
    //10の倍数に切り上げてグラフの見た目を良くする
    const maxUsage = Math.max(...Object.values(cpuData).flat().map(data => data.y));
    const suggestedMax = Math.ceil(maxUsage / 10) * 10;

    return { cpuData, suggestedMax };
    }
    catch (error) {
        console.error("データ取得エラー：", error);
    }
}

//cpuのグラフ色生成
function cpuColor(index) {
    const baseColors = ['#06B6D0', '#8B5CF3', '#F97312', '#DC2620', '#10B982', '#F59E0C', '#EF4445', '#8B5A2C'];
    const colorSteps = 16;

    if (index < baseColors.length) {
        return baseColors[index];
    } else {
        const hue = (index * 360 / colorSteps) % 360;
        return  `hsl(${hue}, 70%, 50%)`;
    }
}

//各モードに応じた時間設定
function getTimeSettings(mode) {
    switch(mode) {
        case 'realtime':
            return {
                unit: 'minute',
                displayFormat: 'HH:mm',
                stepSize: 10,      // 10分ごとに目盛り
                maxTicksLimit: 20, 
                title: '時刻(リアルタイム)'
            };
        case '30minutes':
            return {
                unit: 'minute',
                displayFormat: 'HH:mm', 
                stepSize: 30,      // 30分ごとに目盛り
                maxTicksLimit: 6.5, 
                title: '時刻(10分間隔)'
            };
        case '1hour':
            return {
                unit: 'hour',
                displayFormat: 'HH:mm',
                stepSize: 1,       // 1時間ごとに目盛り
                maxTicksLimit: 4,  // 3時間で4個の目盛り（0,1,2,3時間）
                title: '時刻(1時間間隔)'
            };
        default:
            return {
                unit: 'hour',
                displayFormat: 'HH:mm',
                stepSize: 1,
                maxTicksLimit: 4,
                title: '時刻(1日間隔)'
            };
    }
}

//グローバル変数でcpuChartを定義、生成
let cpuChart = null;

