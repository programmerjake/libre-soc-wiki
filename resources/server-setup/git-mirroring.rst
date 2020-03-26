=======================
Git Mirroring to GitLab
=======================

Steps for setting up automatic mirroring cron jobs:

* Add a new user:

  .. code-block:: bash

    sudo adduser --disabled-login --system git-mirroring

* Start a shell as the `git-mirroring` user:

  .. code-block:: bash

    sudo -H -u git-mirroring /bin/bash

* Switch to home directory:

  .. code-block:: bash

    cd

* Create an executable file `sync.sh` (replace `nano` with the editor of your choice):

  .. code-block:: bash

    touch sync.sh
    chmod +x sync.sh
    nano sync.sh

  * Type in the following contents:

    .. code-block:: bash

      #!/bin/sh
      for repo in ~/*.git; do
          cd "$repo" && git fetch -q && git push -q gitlab || echo "sync failed for $repo"
      done

  * Save and exit the editor.

* Create a ssh key:

  .. code-block:: bash

    ssh-keygen

  Press enter for all prompts -- leaving the file names as default and with an empty password.

* For each repo to be mirrored:

  * Create an empty repo using the GitLab website.

    .. warning::

      Following these steps will overwrite anything that is in the GitLab repo.

  * Add the 
