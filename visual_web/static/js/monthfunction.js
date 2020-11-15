function showAgeOverAll(){
    Plotly.d3.csv("../static/csv/agemonth.csv", function(err, rows){
function unpack(rows, key) {
	return rows.map(function(row)
	{ return row[key]; });}

var trace1 = {
	x:unpack(rows, 'x1'), y: unpack(rows, 'y1'), z: unpack(rows, 'z1'),
    mode: 'markers',
    name: 'Male',
	marker: {
        
        size: 12,
        symbol: 'circle',
		line: {
		color: 'rgba(217, 217, 217, 0.14)',
		width: 0.5},
		opacity: 0.8},
	type: 'scatter3d'
};

var trace2 = {
	x:unpack(rows, 'x2'), y: unpack(rows, 'y2'), z: unpack(rows, 'z2'),
    mode: 'markers',
    name: 'Female',
	marker: {
        
		color: 'rgb(255,105,180)',
		size: 12,
		symbol: 'circle',
		line: {
		color: 'rgb(204, 204, 204)',
		width: 1},
		opacity: 0.8},
	type: 'scatter3d'};

    var data = [trace1, trace2];
    var layout = {margin: {
        l: 0,
        r: 0,
        b: 0,
        t: 0
    }, 
    scene:{
        xaxis: {
        title: 'Month',
         backgroundcolor: "rgb(200, 200, 230)",
         gridcolor: "rgb(255, 255, 255)",
         showbackground: true,
         zerolinecolor: "rgb(255, 255, 255)",
         ticktext:['0','1','2','3','4','5','6','7','8','9','10','11','12'],
        tickvals:[0,1, 2, 3, 4,5,6,7,8,9,10,11,12]
        
        }, 
        yaxis: {
            title: 'Age',
         backgroundcolor: "rgb(230, 200,230)",
         gridcolor: "rgb(255, 255, 255)",
         showbackground: true,
         zerolinecolor: "rgb(255, 255, 255)",
         ticktext:['10-15', '16-20', '21-25','26-30','31-35','36-40'],
         tickvals:[0,1,2,3,4,5],
        
        }, 
        zaxis: {
            title: 'Quantity',
         backgroundcolor: "rgb(230, 230,200)",
         gridcolor: "rgb(255, 255, 255)",
         showbackground: true,
         zerolinecolor: "rgb(255, 255, 255)",
         ticks: 'outside',
       tick0: 0,
        }}
    };
    Plotly.newPlot(document.getElementById("threedchart"), data, layout);
    });
}
