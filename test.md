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

output
```
[route] syntax_ok
[passed] True
[issues] 0
[artifacts] {'tcl': '/home/eda/project/exp/build/review/run_sg_review.tcl', 'errors': '/home/eda/project/exp/build/review/review_errors.txt', 'warnings': '/home/eda/project/exp/build/review/review_warnings.txt', 'raw_log': '/home/eda/project/exp/build/review/review_spyglass.log'}

=== raw log tail ===
Checking Rule Reset_check05 for module TopModule (Rule 215 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule _syncResetStyleRTL for module TopModule (Rule 216 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule _meta_delay01 for module TopModule (Rule 217 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule Ac_svasetup01 for module TopModule (Rule 218 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule LogNMuxPrereq for module TopModule (Rule 219 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule STARC-1.3.2.2_prereq for module TopModule (Rule 220 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule Prereqs_sim_race07 for module TopModule (Rule 221 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule W336 for module TopModule (Rule 222 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule W414 for module TopModule (Rule 223 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule W450L for module TopModule (Rule 224 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule HangingNetPreReq-ML for module TopModule (Rule 225 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule RegInputOutput-ML for module TopModule (Rule 226 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule HVIssue_PreReq for module TopModule (Rule 227 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule STARC05-2.5.1.7 for module TopModule (Rule 228 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule STARC05-2.5.1.9 for module TopModule (Rule 229 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Performing semantic checks on SGDC contents
Checking Rule SGDC_testmode03 (Rule 73 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule _abstractPortSGDC (Rule 230 of total 298) .... done (Time = 0.00s, Memory = 32.0K)
Checking Rule SGDC_abstract_port03 (Rule 231 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule SGDC_abstract_port04 (Rule 232 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule SGDC_abstract_port05 (Rule 233 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule SGDC_abstract_port07 (Rule 234 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule SGDC_abstract_port08 (Rule 235 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule SGDC_abstract_port10 (Rule 236 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule SGDC_abstract_port11 (Rule 237 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule SGDC_abstract_port12 (Rule 238 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule SGDC_abstract_port13 (Rule 239 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule ReportUngroup (Rule 240 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule LINT_portReten (Rule 241 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule SGDC_abstract_port21 (Rule 242 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule InferLatch (Rule 243 of total 298) .... done (Time = 0.00s, Memory = 32.0K)
Checking Rule UndrivenInTerm-ML (Rule 244 of total 298) .... done (Time = 0.00s, Memory = -32.0K)
 Flattening TopModule (.lib instances separately flattened) ....
 Flattening completed
Checking Rule SGDC_set_case_analysis_LC (Rule 245 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule BufClock (Rule 246 of total 298) .... done (Time = 0.00s, Memory = 768.0K)
Checking Rule CombLoop (Rule 247 of total 298) .... done (Time = 0.00s, Memory = 768.0K)
Checking Rule STARC05-2.5.1.2 (Rule 248 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule STARC05-1.3.1.3 (Rule 249 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule STARC05-1.4.3.4 (Rule 250 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule FlopClockConstant (Rule 251 of total 298) .... done (Time = 0.00s, Memory = 8.0K)
Checking Rule FlopSRConst (Rule 252 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule FlopEConst (Rule 253 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule checkPinConnectedToSupply (Rule 254 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule W392 (Rule 255 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule W415 (Rule 256 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule LatchFeedback (Rule 257 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule STARC05-2.4.1.5 (Rule 258 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule STARC05-1.2.1.2 (Rule 259 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule AnalyzeBBox (Rule 260 of total 298) .... done (Time = 0.00s, Memory = 0.0K)
Checking Rule ReportCheckDataSummary (Rule 71 of total 298) .... done (Time = 0.00s, Memory = 0.0K)

Generating data for Console...

SpyGlass Rule Checking Complete.

Generating moresimple report from './review_proj/TopModule/lint/lint_rtl/spyglass.vdb' to './review_proj/TopModule/lint/lint_rtl/spyglass_reports/moresimple.rpt' ....

Generating runsummary report from './review_proj/TopModule/lint/lint_rtl/spyglass.vdb' ....

Generating no_msg_reporting_rules report from './review_proj/TopModule/lint/lint_rtl/spyglass.vdb' to './review_proj/TopModule/lint/lint_rtl/spyglass_reports/no_msg_reporting_rules.rpt' ....

Policy specific data (reports) are present in the directory './review_proj/TopModule/lint/lint_rtl/spyglass_reports'.

SpyGlass critical reports for the current run are present in directory './review_proj/consolidated_reports/TopModule_lint_lint_rtl/'.

---------------------------------------------------------------------------------------------
Results Summary:
---------------------------------------------------------------------------------------------
   Goal Run           :      lint/lint_rtl
   Command-line read  :      0 error,      0 warning,      0 information message
   Design Read        :      0 error,      0 warning,      2 information messages
      Found 1 top module:
         TopModule   (file: TopModule.v)

   Blackbox Resolution:      0 error,      0 warning,      0 information message
   SGDC Checks        :      0 error,      0 warning,      0 information message
   -------------------------------------------------------------------------------------
   Total              :      0 error,      0 warning,      2 information messages

  Total Number of Generated Messages     :         2 (0 error, 0 warning, 2 Infos)
  Number of Reported Messages            :         2 (0 error, 0 warning, 2 Infos)

---------------------------------------------------------------------------------------------


run_goal: info: updating spyglass.log with goal summary
---------------------------------------------------------------------------------------------------
Results Summary:
---------------------------------------------------------------------------------------------------
   Goal Run           :      lint/lint_rtl
   Top Module         :      TopModule
---------------------------------------------------------------------------------------------------
   Reports Directory:
   /home/eda/project/exp/review_proj/consolidated_reports/TopModule_lint_lint_rtl/

   SpyGlass LogFile:
    /home/eda/project/exp/review_proj/TopModule/lint/lint_rtl/spyglass.log

   Standard Reports:
     moresimple.rpt          no_msg_reporting_rules.rpt

   HTML report:
    /home/eda/project/exp/review_proj/html_reports/goals_summary.html


   Technology Reports:
     <Not Available>


---------------------------------------------------------------------------------------------------
   Goal Violation Summary:
       Waived   Messages:                      0 Errors,      0 Warnings,      0 Infos
       Reported Messages:         0 Fatals,    0 Errors,      0 Warnings,      2 Infos
---------------------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------------------

run_goal: info: spyglass.log successfully updated with goal summary
run_goal: info: setting design top `TopModule' as current_design
```



# logic check
run_verify_step3.py 
python eda_generation/run_verify_step3.py   --project-root /home/eda/project/exp   --rtl-flist rtl.f   --tb-flist tb.f   --tb-top tb   --work-subdir .   --sv

output

```
(eda-generation) (base) cognition2@rmd31:~/lin/eda_generation$ python eda_generation/run_verify_step3.py   --project-root /home/eda/project/exp   --rtl-flist rtl.f   --tb-flist tb.f   --tb-top tb   --work-subdir .   --sv
[route] verify_ok
[passed] True
[compile_passed] True
[compile_errors] 0
[failed_cases] 0
[artifacts] {'simv': '/home/eda/project/exp/build/verify/simv', 'compile_log': '/home/eda/project/exp/build/verify/sim_compile.log', 'run_log': '/home/eda/project/exp/build/verify/sim_run.log'}

=== raw log tail ===
VCD info: dumpfile wave.vcd opened for output.
Prob001_zero_test.sv:30: $finish called at 102 (1ps)
Hint: Output 'zero' has no mismatches.
Hint: Total mismatched samples is 0 out of 20 samples

Simulation finished at 102 ps
Mismatches: 0 in 20 samples
```