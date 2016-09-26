from distutils.core import setup

setup(
    name='pycoeman',
    version='1.0.0',
    packages=['pycoeman', 'pycoeman.seqcommands', 'pycoeman.parcommands', 'pycoeman.parcommands.run_parcommands_sge_jobs', 'pycoeman.monitor',],
    license='Apache License 2.0',
    long_description=open('README.md').read(),
    author='Oscar Martinez-Rubi',
    author_email='o.rubi@esciencecenter.nl',
    url='https://github.com/NLeSC/pycoeman',
    install_requires=[
          'numpy', 'tabulate', 'matplotlib', 'lxml', 'pandas', 'paramiko', 'scp'
    ],
    entry_points={
        'console_scripts': [
            'coeman-seq-local=pycoeman.seqcommands.run_seqcommands_local:main',
            'coeman-par-local=pycoeman.parcommands.run_parcommands_local:main',
            'coeman-par-ssh=pycoeman.parcommands.run_parcommands_ssh:main',
            'coeman-par-sge=pycoeman.parcommands.run_parcommands_sge_cluster.run_parcommands_sge_jobs:main',
            'coeman-mon-plot-cpu-mem=pycoeman.monitor.plot_cpu_mem:main',
            'coeman-mon-plot-disk=pycoeman.monitor.plot_disk:main',
            'coeman-mon-stats=pycoeman.monitor.get_monitor_nums:main',
        ],
    },
)
