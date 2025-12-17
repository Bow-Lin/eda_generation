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


# flow 

test_flow.py
```
(eda-generation) (base) cognition2@rmd31:~/lin/eda_generation/eda_generation$ python test_flow.py
{'round': 3, 'last_stage': 'finish', 'review_attempts': 0, 'last_reason': 'verify_fail_limit_reached', 'verify_attempts': 3, 'done': True}
{'phase': 'review', 'tool': 'spyglass(docker)', 'passed': True, 'issues': [], 'artifacts': {'tcl': '/home/eda/project/exp/build/review/run_sg_review.tcl', 'errors': '/home/eda/project/exp/build/review/review_errors.txt', 'warnings': '/home/eda/project/exp/build/review/review_warnings.txt', 'raw_log': '/home/eda/project/exp/build/review/review_spyglass.log'}, 'raw_log_tail': ['Checking Rule SGDC_waive03 (Rule 24 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive04 (Rule 25 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive05 (Rule 26 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive06 (Rule 27 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive07 (Rule 28 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive08 (Rule 29 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive09 (Rule 30 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive10 (Rule 31 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive11 (Rule 32 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive12 (Rule 33 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive13 (Rule 34 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive21 (Rule 35 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive22 (Rule 36 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive30 (Rule 37 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive32 (Rule 38 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive33 (Rule 39 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive36 (Rule 40 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_waive38 (Rule 41 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_fifo01 (Rule 42 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_libgroup01 (Rule 43 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_libgroup02 (Rule 44 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_libgroup04 (Rule 45 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_power_data01 (Rule 46 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_ungroup01 (Rule 47 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_abstract_port06 (Rule 48 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_abstract_port14 (Rule 49 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule SGDC_abstract_port15 (Rule 50 of total 298) .... done (Time = 0.00s, Memory = 16.0K)', 'Checking Rule SGDC_abstract_port18 (Rule 51 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule sdc_init_rule (Rule 52 of total 298) .... done (Time = 0.00s, Memory = -32.0K)', 'Checking Rule CMD_ignorelibs01 (Rule 53 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule ReportRuleNotRun (Rule 54 of total 298) .... done (Time = 0.01s, Memory = 0.0K)', 'Checking Rule STARC05-2.3.1.2c (Rule 55 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule W442a (Rule 56 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule W442b (Rule 57 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule W442c (Rule 58 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule W442f (Rule 59 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule mixedsenselist (Rule 60 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule badimplicitSM1 (Rule 61 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule badimplicitSM2 (Rule 62 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule badimplicitSM4 (Rule 63 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule bothedges (Rule 64 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule BlockHeader (Rule 65 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule W421 (Rule 66 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule STARC05-2.1.6.5 (Rule 67 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule ReportStopSummary (Rule 68 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', 'Checking Rule ReportIgnoreSummary (Rule 69 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', ' Analyzing source file "TopModule.v" ....', ' Analyzing source file "Prob001_zero_ref.sv" ....', '***Syntax Errors detected - RULE CHECKING ABORTED***', 'Checking Rule ReportCheckDataSummary (Rule 70 of total 298) .... done (Time = 0.00s, Memory = 0.0K)', '', 'SpyGlass Rule Checking ABORTED.', '', 'Generating data for Console...', '', "Generating moresimple report from './review_proj/TopModule/lint/lint_rtl/spyglass.vdb' to './review_proj/TopModule/lint/lint_rtl/spyglass_reports/moresimple.rpt' ....", '', "Generating runsummary report from './review_proj/TopModule/lint/lint_rtl/spyglass.vdb' ....", '', "Generating no_msg_reporting_rules report from './review_proj/TopModule/lint/lint_rtl/spyglass.vdb' to './review_proj/TopModule/lint/lint_rtl/spyglass_reports/no_msg_reporting_rules.rpt' ....", '', "Policy specific data (reports) are present in the directory './review_proj/TopModule/lint/lint_rtl/spyglass_reports'.", '', "SpyGlass critical reports for the current run are present in directory './review_proj/consolidated_reports/TopModule_lint_lint_rtl/'.", '', '---------------------------------------------------------------------------------------------', 'Results Summary:', '---------------------------------------------------------------------------------------------', '   Goal Run           :      lint/lint_rtl', '** Design Read        :      1 fatal,      0 error,        0 warning,      0 information message ', '   -------------------------------------------------------------------------------------', '** Total              :      1 fatal,      0 error,        0 warning,      0 information message ', '', '  Total Number of Generated Messages     :         1 (1 fatal, 0 error, 0 warning, 0 Info)', '  Number of Reported Messages            :         1 (1 fatal, 0 error, 0 warning, 0 Info)', '', '  NOTE: It is recommended to first fix/reconcile fatals/errors reported on', '        lines starting with ** as subsequent issues might be related to it.', '        Please re-run SpyGlass once ** prefixed lines are fatal/error clean.', '', '---------------------------------------------------------------------------------------------', '', 'Following FATAL message(s) generated in current run -', '', 'Rule         Severity   File          Line   Message', '-------------------------------------------------------------------------', "STX_VE_479   Syntax     TopModule.v   2      Syntax error near ( out ). Please use 'set_option enableSV yes' to support SystemVerilog construct ( logic )", 'run_goal: info: updating spyglass.log with goal summary', '---------------------------------------------------------------------------------------------------', 'Results Summary:', '---------------------------------------------------------------------------------------------------', '   Goal Run           :      lint/lint_rtl', '   Top Module         :      TopModule', '---------------------------------------------------------------------------------------------------', '   Reports Directory: ', '   /home/eda/project/exp/review_proj/consolidated_reports/TopModule_lint_lint_rtl/ ', '', '   SpyGlass LogFile: ', '    /home/eda/project/exp/review_proj/TopModule/lint/lint_rtl/spyglass.log ', '', '   Standard Reports: ', '     moresimple.rpt          no_msg_reporting_rules.rpt       ', '', '   HTML report:', '    /home/eda/project/exp/review_proj/html_reports/goals_summary.html', '  ', '', '   Technology Reports:  ', '     <Not Available>', '   ', '   ', '---------------------------------------------------------------------------------------------------', '   Goal Violation Summary:', '       Waived   Messages:                      0 Errors,      0 Warnings,      0 Infos', '       Reported Messages:         1 Fatals,    0 Errors,      0 Warnings,      0 Infos', '---------------------------------------------------------------------------------------------------', '   ', '---------------------------------------------------------------------------------------------------', ' ', 'run_goal: info: spyglass.log successfully updated with goal summary']}
{'phase': 'verify', 'tool': 'iverilog', 'passed': False, 'skipped': False, 'compile_passed': False, 'compile_errors': [{'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 16, 'message': 'Task/function default argument requires SystemVerilog.', 'context': ['14: //    output reg wavedrom_enable', '15: ', '16: \ttask wavedrom_start(input[511:0] title = "");', '17: \tendtask', '18: \t']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 16, 'message': 'Task body with no statements requires SystemVerilog.', 'context': ['14: //    output reg wavedrom_enable', '15: ', '16: \ttask wavedrom_start(input[511:0] title = "");', '17: \tendtask', '18: \t']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 37, 'message': 'syntax error', 'context': ['35: module tb();', '36: ', '37: \ttypedef struct packed {', '38: \t\tint errors;', '39: \t\tint errortime;']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 37, 'message': 'Invalid module instantiation', 'context': ['35: module tb();', '36: ', '37: \ttypedef struct packed {', '38: \t\tint errors;', '39: \t\tint errortime;']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 39, 'message': 'syntax error', 'context': ['37: \ttypedef struct packed {', '38: \t\tint errors;', '39: \t\tint errortime;', '40: \t\tint errors_zero;', '41: \t\tint errortime_zero;']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 39, 'message': 'Invalid module instantiation', 'context': ['37: \ttypedef struct packed {', '38: \t\tint errors;', '39: \t\tint errortime;', '40: \t\tint errors_zero;', '41: \t\tint errortime_zero;']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 40, 'message': 'syntax error', 'context': ['38: \t\tint errors;', '39: \t\tint errortime;', '40: \t\tint errors_zero;', '41: \t\tint errortime_zero;', '42: ']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 40, 'message': 'Invalid module instantiation', 'context': ['38: \t\tint errors;', '39: \t\tint errortime;', '40: \t\tint errors_zero;', '41: \t\tint errortime_zero;', '42: ']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 41, 'message': 'syntax error', 'context': ['39: \t\tint errortime;', '40: \t\tint errors_zero;', '41: \t\tint errortime_zero;', '42: ', '43: \t\tint clocks;']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 41, 'message': 'Invalid module instantiation', 'context': ['39: \t\tint errortime;', '40: \t\tint errors_zero;', '41: \t\tint errortime_zero;', '42: ', '43: \t\tint clocks;']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 43, 'message': 'syntax error', 'context': ['41: \t\tint errortime_zero;', '42: ', '43: \t\tint clocks;', '44: \t} stats;', '45: \t']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 43, 'message': 'Invalid module instantiation', 'context': ['41: \t\tint errortime_zero;', '42: ', '43: \t\tint clocks;', '44: \t} stats;', '45: \t']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 44, 'message': 'Invalid module item.', 'context': ['42: ', '43: \t\tint clocks;', '44: \t} stats;', '45: \t', '46: \tstats stats1;']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 46, 'message': 'syntax error', 'context': ['44: \t} stats;', '45: \t', '46: \tstats stats1;', '47: \t', '48: \t']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 46, 'message': 'Invalid module instantiation', 'context': ['44: \t} stats;', '45: \t', '46: \tstats stats1;', '47: \t', '48: \t']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 51, 'message': 'syntax error', 'context': ['49: \twire[511:0] wavedrom_title;', '50: \twire wavedrom_enable;', '51: \tint wavedrom_hide_after_time;', '52: \t', '53: \treg clk=0;']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 51, 'message': 'Invalid module instantiation', 'context': ['49: \twire[511:0] wavedrom_title;', '50: \twire wavedrom_enable;', '51: \tint wavedrom_hide_after_time;', '52: \t', '53: \treg clk=0;']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 79, 'message': 'syntax error', 'context': ['77: ', '78: \t', '79: \tbit strobe = 0;', '80: \ttask wait_for_end_of_timestep;', '81: \t\trepeat(5) begin']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 79, 'message': 'Invalid module instantiation', 'context': ['77: ', '78: \t', '79: \tbit strobe = 0;', '80: \ttask wait_for_end_of_timestep;', '81: \t\trepeat(5) begin']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 88, 'message': 'syntax error', 'context': ['86: ', '87: \t', '88: \tfinal begin', '89: \t\tif (stats1.errors_zero) $display("Hint: Output \'%s\' has %0d mismatches. First mismatch occurred at time %0d.", "zero", stats1.errors_zero, stats1.errortime_zero);', '90: \t\telse $display("Hint: Output \'%s\' has no mismatches.", "zero");']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 88, 'message': 'Invalid module instantiation', 'context': ['86: ', '87: \t', '88: \tfinal begin', '89: \t\tif (stats1.errors_zero) $display("Hint: Output \'%s\' has %0d mismatches. First mismatch occurred at time %0d.", "zero", stats1.errors_zero, stats1.errortime_zero);', '90: \t\telse $display("Hint: Output \'%s\' has no mismatches.", "zero");']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 90, 'message': 'Invalid module item.', 'context': ['88: \tfinal begin', '89: \t\tif (stats1.errors_zero) $display("Hint: Output \'%s\' has %0d mismatches. First mismatch occurred at time %0d.", "zero", stats1.errors_zero, stats1.errortime_zero);', '90: \t\telse $display("Hint: Output \'%s\' has no mismatches.", "zero");', '91: ', '92: \t\t$display("Hint: Total mismatched samples is %1d out of %1d samples\\n", stats1.errors, stats1.clocks);']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 95, 'message': 'syntax error', 'context': ['93: \t\t$display("Simulation finished at %0d ps", $time);', '94: \t\t$display("Mismatches: %1d in %1d samples", stats1.errors, stats1.clocks);', '95: \tend', '96: \t', '97: \t// Verification: XORs on the right makes any X in good_vector match anything, but X in dut_vector will only match X.']}, {'severity': 'Error', 'file': 'Prob001_zero_test.sv', 'line': 98, 'message': 'Invalid module item.', 'context': ['96: \t', '97: \t// Verification: XORs on the right makes any X in good_vector match anything, but X in dut_vector will only match X.', '98: \tassign tb_match = ( { zero_ref } === ( { zero_ref } ^ { zero_dut } ^ { zero_ref } ) );', '99: \t// Use explicit sensitivity list here. @(*) causes NetProc::nex_input() to be called when trying to compute', "100: \t// the sensitivity list of the @(strobe) process, which isn't implemented."]}], 'failed_cases': [], 'artifacts': {'simv': '/home/eda/project/exp/build/verify/simv', 'compile_log': '/home/eda/project/exp/build/verify/sim_compile.log', 'run_log': '/home/eda/project/exp/build/verify/sim_run.log'}, 'raw_log_tail': ['Prob001_zero_test.sv:16: error: Task/function default argument requires SystemVerilog.', 'Prob001_zero_test.sv:16: error: Task body with no statements requires SystemVerilog.', 'Prob001_zero_test.sv:37: syntax error', 'Prob001_zero_test.sv:37: error: Invalid module instantiation', 'Prob001_zero_test.sv:39: syntax error', 'Prob001_zero_test.sv:39: error: Invalid module instantiation', 'Prob001_zero_test.sv:40: syntax error', 'Prob001_zero_test.sv:40: error: Invalid module instantiation', 'Prob001_zero_test.sv:41: syntax error', 'Prob001_zero_test.sv:41: error: Invalid module instantiation', 'Prob001_zero_test.sv:43: syntax error', 'Prob001_zero_test.sv:43: error: Invalid module instantiation', 'Prob001_zero_test.sv:44: error: Invalid module item.', 'Prob001_zero_test.sv:46: syntax error', 'Prob001_zero_test.sv:46: error: Invalid module instantiation', 'Prob001_zero_test.sv:51: syntax error', 'Prob001_zero_test.sv:51: error: Invalid module instantiation', 'Prob001_zero_test.sv:79: syntax error', 'Prob001_zero_test.sv:79: error: Invalid module instantiation', 'Prob001_zero_test.sv:88: syntax error', 'Prob001_zero_test.sv:88: error: Invalid module instantiation', 'Prob001_zero_test.sv:90: error: Invalid module item.', 'Prob001_zero_test.sv:95: syntax error', 'Prob001_zero_test.sv:98: error: Invalid module item.']}
```