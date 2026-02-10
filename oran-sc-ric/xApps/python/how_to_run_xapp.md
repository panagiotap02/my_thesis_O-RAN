## Commands to run an xAPP

> Requirement: The docker compose from /home/panagiotopoulou/clean/oran-sc-ric/docker-compose.yml must already be running (go to /home/panagiotopoulou/clean/oran-sc-ric and run: docker compose up)

### Run the kpm_mon_xapp
``` bash
cd /home/panagiotopoulou/clean/oran-sc-ric
docker compose exec python_xapp_runner ./kpm_mon_xapp.py --metrics=DRB.UEThpDl,DRB.UEThpUl --kpm_report_style=1
```

### Run the my_smart_xapp
``` bash
cd /home/panagiotopoulou/clean/oran-sc-ric
docker compose exec python_xapp_runner ./my_smart_xapp.py --metrics=DRB.UEThpDl,DRB.UEThpUl --kpm_report_style=1
```
