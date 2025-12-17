# rtl generation 
run_code_agent_step1.py

python eda_generation/run_code_agent_step1.py --spec "TODO: your spec" --project-root /exp

rtl code will be saved to /exp

# syntax check
run_review_step2.py

python eda_generation/run_review_step2.py \
  --project-root /home/eda/project/exp \
  --rtl-flist rtl.f \
  --top-rtl TopModule \
  --work-subdir . \
  --container-name spyglass-centos7 \
  --docker-bin docker
