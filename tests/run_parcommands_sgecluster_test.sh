python ../pycoeman/parcommands/run_parcommands_sge_cluster/create_parcommands_sge_jobs.py -d . -c parcommands_test.xml -s /home/orubi/improphoto/export_paths.sh -r /local/orubi/TestPycoeman -o parcommands_sgecluster_test_out -q parcommands_sgecluster_test_submit.sh
chmod u+x parcommands_sgecluster_test_submit.sh
./parcommands_sgecluster_test_submit.sh
