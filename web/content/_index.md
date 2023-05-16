---
title: Your Good Governance initiative
date: [GGI_CURRENT_DATE]
layout: default
---

{{% content "includes/initialisation.inc" %}}

## General progress

<div class="w3-row">
  <div class="w3-half w3-container">
<p>Activities:</p>
{{% content "includes/activities_stats_dashboard.inc" %}}
  </div>
  <div class="w3-half w3-container">
<canvas id="allActivities" style="width:100%;max-width:400px"></canvas>
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
  </div>
</div> 

## Goals

<canvas id="myGoals" style="width:100%;max-width:700px"></canvas>
<script>
labels = ['Usage', 'Trust', 'Culture', 'Engagement', 'Strategy'];
data = {
  labels: labels,
  datasets: [
    {
      label: 'Done',
      data: {{% content "includes/ggi_data_goals_done.inc" %}},
      backgroundColor: 'rgb(255, 205, 86)',
    },
    {
      label: 'In Progress',
      data: {{% content "includes/ggi_data_goals_in_progress.inc" %}},
      backgroundColor: 'rgb(54, 162, 235)',
    },
    {
      label: 'Not Started',
       data: {{% content "includes/ggi_data_goals_not_started.inc" %}},
      backgroundColor: 'rgb(255, 99, 132)',
    },
  ]
};
new Chart("myGoals", {
    type: 'bar',
    data: data,
    responsive: true,
    options: {
      scales: {
        xAxes: [{
	  stacked: true,
	}],
        yAxes: [{
          beginAtZero: true,
	  stacked: true
	}]
      }
    }
  }
);

</script>


## Current activities <a href='current_activities' class='w3-text-grey' style="float:right">[ details ]</a> 

Current activities are defined as having the label <span class="w3-tag w3-light-grey">in_progress</span>. <br />
These are your current activities:

{{% content "includes/current_activities.inc" %}}

See the detailed list of [current activities](current_activities).


## Completed activities <a href='past_activities' class='w3-text-grey' style="float:right">[ details ]</a>

Completed activities are defined as having the label <span class="w3-tag w3-light-grey">done</span>. <br />
These are your completed activities:

{{% content "includes/past_activities.inc" %}}

See the detailed list of [completed activities](past_activities).

## Resources

The [Good Governance Initiative Handbook](https://ospo.zone/ggi) is developed by the OSPO Alliance. 

Check [our website](https://ospo.zone) and [join the discussion](https://accounts.eclipse.org/mailing-list/ospo.zone)!
