#!/usr/bin/env bash
python ../pycoeman/parcommands/run_parcommands_sge_cluster/run_parcommands_sge_jobs.py -d . -c parcommands_test.xml -s /home/orubi/improphoto/export_paths.sh -r /local/orubi/TestPycoeman -o parcommands_sge_cluster_test_out
