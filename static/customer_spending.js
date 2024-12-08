google.charts.load("current", { packages: ["corechart", "bar"] });
google.charts.setOnLoadCallback(drawBarChart);

function drawBarChart() {
  if (!months.length || !monthly_spendings.length) {
    console.error("No data available to render the chart.");
    document.getElementById("cusMonthlySpending").innerText = "No spending data available for the selected period.";
    return;
  }

  let dataContent = [["Month", "Spending"]];
  for (let i = 0; i < months.length; i++) {
    dataContent.push([months[i], monthly_spendings[i]]);
  }

  const data = google.visualization.arrayToDataTable(dataContent);

  const options = {
    title: "Monthly Spending",
    legend: { position: "none" },
    hAxis: {
      title: "Months",
    },
    vAxis: {
      title: "Spending (USD)",
    },
    bar: { groupWidth: "50%" },
  };

  const chart = new google.visualization.ColumnChart(
    document.getElementById("cusMonthlySpending")
  );
  chart.draw(data, options);
}
