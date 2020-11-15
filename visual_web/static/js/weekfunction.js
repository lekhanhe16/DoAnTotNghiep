var female = [0, 0, 0, 0, 0, 0]
var male = [0, 0, 0, 0, 0, 0]
function showBarChart(fetch_data){
    var quantityEachRange = countQ(fetch_data);
    
    var ctx = document.getElementById("barChart").getContext('2d');
    return new Chart(ctx, {
    type: 'bar',
    data: {
    labels: ["10-15", "16-20", "21-25", "26-30", "31-35", "36-40"],
    datasets: [{
    label: 'Num of persons',
    data: quantityEachRange, 
    backgroundColor: [
    'rgba(255, 99, 132, 0.2)',
    'rgba(54, 162, 235, 0.2)',
    'rgba(255, 206, 86, 0.2)',
    'rgba(75, 192, 192, 0.2)',
    'rgba(153, 102, 255, 0.2)',
    'rgba(255, 159, 64, 0.2)'
    ],
    borderColor: [
    'rgba(255,99,132,1)',
    'rgba(54, 162, 235, 1)',
    'rgba(255, 206, 86, 1)',
    'rgba(75, 192, 192, 1)',
    'rgba(153, 102, 255, 1)',
    'rgba(255, 159, 64, 1)'
    ],
    borderWidth: 1}]
    },
    options: {scales: {yAxes: [{ticks: {beginAtZero: true}}]}}
    });
}

function showPolarChart(chart){
    
    var ds = (chart == "polarChart") ? male : female;
    
    var ctxPA = document.getElementById(chart).getContext('2d');
    return new Chart(ctxPA, {
    type: 'polarArea',
    data: {
    labels: ["10-15", "16-20", "21-25", "26-30", "31-35", "36-40"],
    datasets: [{
    data: ds,
    backgroundColor: ["rgba(219, 0, 0, 0.1)", "rgba(0, 165, 2, 0.1)", "rgba(255, 195, 15, 0.2)",
    "rgba(55, 59, 66, 0.1)", "rgba(0, 0, 0, 0.3)"
    ],
    hoverBackgroundColor: ["rgba(219, 0, 0, 0.2)", "rgba(0, 165, 2, 0.2)",
    "rgba(255, 195, 15, 0.3)", "rgba(55, 59, 66, 0.1)", "rgba(0, 0, 0, 0.4)"
    ]
    }]
    },
    options: {
    responsive: true
    }
    });
}
function countQ(data){
    var r = [0,0,0,0,0,0];
    for(d of data){
        var age = d.lower + 3;
        if(age>=10 && age<=15) {r[0]++; 
        female[0] = (d.gender == 0) ? female[0]+1 : female[0]; 
        male[0] = (d.gender == 1) ? male[0]+1 : male[0];}

        else if(age>=16 && age<=20) {r[1]++;
        female[1] = (d.gender == 0) ? female[1]+1 : female[1]; 
        male[1] = (d.gender == 1) ? male[1]+1 : male[1];}

        else if(age >=21 && age<=25) {r[2]++;
        female[2] = (d.gender == 0) ? female[2]+1 : female[2]; 
        male[2] = (d.gender == 1) ? male[2]+1 : male[2];}

        else if(age >=26 && age<=30) {r[3]++;
        female[3] = (d.gender == 0) ? female[3]+1 : female[3]; 
        male[3] = (d.gender == 1) ? male[3]+1 : male[3];}

        else if(age >=31 && age<=35) {r[4]++;
        female[4] = (d.gender == 0) ? female[4]+1 : female[4]; 
        male[4] = (d.gender == 1) ? male[4]+1 : male[4];}

        else if(age >=36 && age<=40) {r[5]++;
        female[5] = (d.gender == 0) ? female[5]+1 : female[5]; 
        male[5] = (d.gender == 1) ? male[5]+1 : male[5];}
    }
    return r;
}

