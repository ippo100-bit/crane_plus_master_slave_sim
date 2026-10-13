from glob import glob

from setuptools import setup

package_name = 'crane_plus_master_slave_sim'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
        ('share/' + package_name + '/rviz', glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ippo100-bit',
    maintainer_email='noreply@example.com',
    description='Reproduce CRANE+ V2 master-slave teleoperation with two arms in RViz.',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'master_slave_bridge = crane_plus_master_slave_sim.master_slave_bridge:main',
        ],
    },
)
