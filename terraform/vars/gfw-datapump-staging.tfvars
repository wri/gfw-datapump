environment = "staging"

lambda_submit_job_runtime     = "python3.7"
lambda_submit_job_memory_size = 1024
lambda_submit_job_timeout     = 300

lambda_upload_results_runtime     = "python3.7"
lambda_upload_results_memory_size = 1024
lambda_upload_results_timeout     = 300

lambda_check_datasets_runtime     = "python3.7"
lambda_check_datasets_memory_size = 1024
lambda_check_datasets_timeout     = 300

lambda_check_new_aoi_runtime     = "python3.7"
lambda_check_new_aoi_memory_size = 3008
lambda_check_new_aoi_timeout     = 900

lambda_update_new_aoi_statuses_runtime     = "python3.7"
lambda_update_new_aoi_statuses_memory_size = 3008
lambda_update_new_aoi_statuses_timeout     = 900

lambda_check_new_glad_alerts_runtime     = "python3.7"
lambda_check_new_glad_alerts_memory_size = 1024
lambda_check_new_glad_alerts_timeout     = 300

lambda_get_latest_fire_alerts_runtime     = "python3.6"
lambda_get_latest_fire_alerts_memory_size = 3008
lambda_get_latest_fire_alerts_timeout     = 900

geotrellis_jar = "s3://gfw-pipelines-staging/geotrellis/jars/treecoverloss-assembly-1.1.0.jar"

datasets = {
  "geostore": {
    "annualupdate_minimal": {
      "change" = "952f3a90-ea03-4bf7-93a7-5ffbca48248d"
      "summary" = "8a857b48-971d-4358-bd91-243d248ec713"
      "whitelist" = "2508ebe7-ee26-4ddd-aeb1-d7e6d2772ccb"
    }
    "gladalerts": {
      "daily_alerts" = "23483d57-4bf7-426a-903b-b917a335eec0"
      "weekly_alerts" = "3172b978-3ef1-4e01-8943-03a4c259f12f"
      "summary" = "489a5e5d-067f-4528-9395-a20c86ed329e"
      "whitelist" = "cc0a64f1-a656-42f0-9383-7f1b68b4e46b"
    }
    "firealerts_modis": {
      "daily_alerts" = "c0254765-e921-45e5-9eed-72b7294ce150"
      "weekly_alerts" = "5586eb14-8016-4630-8e2b-7636a0b26983"
      "whitelist" = "fab92867-45f0-4e47-af4e-73ea6b9372e3"
    }
    "firealerts_viirs": {
      "daily_alerts" = "5d7305db-e074-4e33-b011-c34dc09709ba"
      "weekly_alerts" = "290fa76b-d954-4473-bef2-b7e89f778436"
      "whitelist" = "4e0cd805-2339-41ce-af02-8ab093ce7ebc"
    }
  }
  "gadm": {
    "gladalerts": {
      "iso": {
        "weekly_alerts" = "f79d86c8-e1f7-4611-8172-5ab029c45c8d"
      }
      "adm1": {
        "weekly_alerts" = "2c192cfd-52d2-440b-85c1-4496b7cf3de7"
      }
      "adm2": {
        "daily_alerts" = "f328893b-1a53-4d11-b00a-e6f5767db1be",
        "weekly_alerts" = "a6195a49-7d58-4284-af29-24dc7ddd627f"
      }
    }
    "firealerts_viirs": {
      "iso": {
        "weekly_alerts" = "a4a60110-8465-4f1f-ace1-1be1f3f19446"
      }
      "adm1": {
        "weekly_alerts" = "0470e566-5ec3-4d23-b4dd-1d0eb42208b5"
      }
      "adm2": {
        "daily_alerts" = "fefec43c-c9fa-40f0-bac7-616338514bc1"
        "weekly_alerts" = "6bf23a98-3e76-43e6-876c-68a11abf7f8c"
      }
    }
    "firealerts_modis": {
      "iso": {
        "weekly_alerts" = "58fee933-81bd-45bd-a1eb-6a37972e7c28"
      }
      "adm1": {
        "weekly_alerts" = "aae20051-c216-4b42-96d0-e8befc34f1cf"
      }
      "adm2": {
        "daily_alerts" = "7dfa052a-155a-4159-b3ba-d0f81152662e"
        "weekly_alerts" = "03e08f73-135a-464d-9ec3-ded08e6c69dd"
      }
    }
  }
  "wdpa": {
    "gladalerts": {
      "daily_alerts" = "99b1e1ea-eea8-4212-9868-ee4b69f1b268",
      "weekly_alerts" = "7e0669c2-e35b-4fa4-9e06-7a3c8e0cd767"
    }
    "firealerts_modis": {
      "daily_alerts" = "5be51b58-43f7-4973-aebf-46ae11ac62ba"
      "weekly_alerts" = "a1e38d65-1e1f-4e2c-ba66-f7c449a82a9a"
    }
    "firealerts_viirs": {
      "daily_alerts" = "c8040782-9dbb-4f6a-a8f8-51d43afdf81a"
      "weekly_alerts" = "9b984feb-2d16-4414-9bf2-08235e3f3cc5"
    }
  }
}