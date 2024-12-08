google.charts.load("current", { packages: ["bar"] });
google.charts.setOnLoadCallback(drawBarChart2);

const person6 = ppl2[0];
const person7 = ppl2[1];
const person8 = ppl2[2];
const person9 = ppl2[3];
const person10 = ppl2[4];
const commission6 = commissions[0];
const commission7 = commissions[1];
const commission8 = commissions[2];
const commission9 = commissions[3];
const commission10 = commissions[4];

function drawBarChart2() {
  var data = new google.visualization.arrayToDataTable([
    ["Commission", "amount of commission"],
    [person6, commission6],
    [person7, commission7],
    [person8, commission8],
    [person9, commission9],
    [person10, commission10],
  ]);

  var options = {
    legend: { position: "none" },
    chart: {
      title: "Top 5 Customers",
      subtitle: "based on amount of commission in the past year",
    },
    axes: {
      x: {
        0: { side: "bottom", label: "amount of commission in the past year" },
      },
    },
    bar: { groupWidth: "50%" },
  };

  var chart = new google.charts.Bar(document.getElementById("right"));
  chart.draw(data, google.charts.Bar.convertOptions(options));
}
