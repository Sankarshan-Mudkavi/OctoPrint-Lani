# -*- mode: ruby -*-
# vi: set ft=ruby :

HOSTNAME = 'octoprint.vlan.lanilabs.com'

Vagrant.configure(2) do |config|
  config.vm.provider 'virtualbox' do |vbox|
    vbox.memory = '1024'
  end

  config.vm.define HOSTNAME, primary: true do |rpi|
    rpi.vm.box = 'debian/jessie64'

    rpi.vm.provider 'virtualbox' do |vbox|
      vbox.name = HOSTNAME
    end

    rpi.vm.network 'private_network', ip: '10.0.0.200'
    rpi.vm.synced_folder './', '/usr/local/src/OctoPrint-Lani', type: 'nfs', mount_options: ['rw', 'vers=3', 'tcp', 'fsc' ,'actimeo=2']

    rpi.vm.provision 'shell', privileged: true, inline: <<-SHELL
      echo 'Setting hostname...'
      hostnamectl set-hostname ${HOSTNAME}

      echo 'Updating packages...'
      apt-get update
      apt-get upgrade -y

      echo 'Installing dependencies...'
      apt-get install -y curl git vim python-dev build-essential
      curl https://bootstrap.pypa.io/get-pip.py | sudo python -
      pip install virtualenv

      echo 'Creating virtual environment...'
      virtualenv /home/vagrant/lanibox/env

      echo 'Cloning OctoPrint...'
      cd /home/vagrant/lanibox
      git clone https://github.com/foosel/OctoPrint

      echo 'Activating virtual environment for the rest of setup...'
      source /home/vagrant/lanibox/env/bin/activate

      echo 'Installing OctoPrint to virtual environment...'
      pip install -e /home/vagrant/lanibox/OctoPrint

      echo 'Installing Lani plugin...'
      cd /usr/local/src/OctoPrint-Lani
      python setup.py develop

      echo 'Changing ownership of lanibox folder...'
      chown -R vagrant: /home/vagrant/lanibox

      echo 'Activating virtual environment for every session...'
      echo 'source /home/vagrant/lanibox/env/bin/activate' >> /home/vagrant/.bashrc

      echo 'Creating aliases...'
      echo "alias seba='source /home/vagrant/lanibox/env/bin/activate'" >> /home/vagrant/.bashrc
      echo "alias oprint='octoprint'" >> /home/vagrant/.bashrc

      echo 'echo "Use oprint command to start app."' >> /home/vagrant/.bashrc

      echo 'Done.'
    SHELL
  end
end
