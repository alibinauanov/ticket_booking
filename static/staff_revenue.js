google.charts.load('current', {'packages':['corechart']});
google.charts.setOnLoadCallback(drawChart);

const mdirect0 = mdirect[0];
const mindirect0 = mindirect[0];
mdirect0
function drawChart() {

  var data = google.visualization.arrayToDataTable([
    ['Sales', 'Amount'],
    ['Direct(bought by customer)', mdirect0],
    ['Indirect(bought through agent)', mindirect0],

  ]);

  var options = {
    title: 'Total Revenue Last Month'
  };

  var chart = new google.visualization.PieChart(document.getElementById('revenue_chart'));

  chart.draw(data, options);
}
