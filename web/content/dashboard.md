---
title: My Dashboard
date: [GGI_CURRENT_DATE]
layout: default
---

## General progress

<canvas id="allActivities" style="width:100%;max-width:700px"></canvas>
<script>
data = {
  labels: [
    'Not Started',
    'In Progress',
    'Done'
  ],
  datasets: [{
    label: 'My activities',
    data: {{% content "includes/ggi_data_all_activities.inc" %}},
    backgroundColor: [
      'rgb(255, 99, 132)',
      'rgb(54, 162, 235)',
      'rgb(255, 205, 86)'
    ],
    hoverOffset: 4
  }]
};

new Chart("allActivities", {
  type: "doughnut",
  data: data
});
</script>

## Goals

<canvas id="myGoals" style="width:100%;max-width:700px"></canvas>
<script>
labels = ['a', 'b', 'c', 'd', 'e', 'f', 'g'];
data = {
  labels: labels,
  datasets: [{
    label: 'My First Dataset',
    data: [65, 59, 80, 81, 56, 55, 40],
    backgroundColor: [
      'rgba(255, 99, 132, 0.2)',
      'rgba(255, 159, 64, 0.2)',
      'rgba(255, 205, 86, 0.2)',
      'rgba(75, 192, 192, 0.2)',
      'rgba(54, 162, 235, 0.2)',
      'rgba(153, 102, 255, 0.2)',
      'rgba(201, 203, 207, 0.2)'
    ],
    borderColor: [
      'rgb(255, 99, 132)',
      'rgb(255, 159, 64)',
      'rgb(255, 205, 86)',
      'rgb(75, 192, 192)',
      'rgb(54, 162, 235)',
      'rgb(153, 102, 255)',
      'rgb(201, 203, 207)'
    ],
    borderWidth: 1
  }]
};

new Chart("myGoals", {
    type: 'bar',
    data: data,
    options: {
      scales: {
        y: {beginAtZero: true}
      }
}});

</script>

## Your dashboard - radar

<canvas id="myChart" style="width:100%;max-width:700px"></canvas>
<script>
const data = {
  labels: [
    'Usage Goal',
    'Trust Goal',
    'Culture Goal',
    'Engagement Goal',
    'Strategy Goal'
  ],
  datasets: [{
    label: 'My First Dataset',
    data: [5, 4, 2, 2, 1],
    fill: true,
    backgroundColor: 'rgba(255, 99, 132, 0.2)',
    borderColor: 'rgb(255, 99, 132)',
    pointBackgroundColor: 'rgb(255, 99, 132)',
    pointBorderColor: '#fff',
    pointHoverBackgroundColor: '#fff',
    pointHoverBorderColor: 'rgb(255, 99, 132)'
  }]
};

new Chart("myChart", {
  type: "radar",
  data: data,
  options: {
    elements: {
      line: {
        borderWidth: 3
      }
    },
    scales: {
        r: {
            suggestedMin: 0,
            suggestedMax: 5
        }
    }
  },
});
</script>
