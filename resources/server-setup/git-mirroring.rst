=======================
Git Mirroring to GitLab
=======================

Steps for setting up automatic mirroring cron jobs:

#) Add a new user:

   .. code:: bash

     sudo adduser --disabled-login --system git-mirroring

#) Start a shell as the :code:`git-mirroring` user:

   .. code:: bash

     sudo -H -u git-mirroring /bin/bash

#) Switch to the home directory:

   .. code:: bash

     cd

#) Create an executable file :code:`sync.sh` (replace :code:`nano` with the editor of your choice):

   .. code:: bash

     touch sync.sh
     chmod +x sync.sh
     nano sync.sh

   a) Type in the following contents:

      .. code:: bash

        #!/bin/sh
        for repo in ~/*.git; do
            cd "$repo" && git fetch -q && git push -q gitlab || echo "sync failed for $repo"
        done

   #) Save and exit the editor.

#) Create a ssh key:

   .. code:: bash

     ssh-keygen

   Press enter for all prompts -- leaving the file names as default and with an empty password.

#) For each repo to be mirrored:

   In the following commands, replace :code:`$UPSTREAM_URL` with the url for the upstream repo, :code:`$NAME` with the name selected for the local directory.

   a) Create an empty repo using the GitLab website.

      .. warning::

        Following these steps will overwrite anything that is in the GitLab repo.

   In the following commands, replace :code:`$MIRROR_URL` with the ssh url for the mirror, you can get it by clicking the Clone button for the empty repo you just created.

   b) Add the ssh key for the :code:`git-mirroring` user to the GitLab repo as a `deploy key with read/write access <https://docs.gitlab.com/ce/ssh/#per-repository-deploy-keys>`_:

      Get the ssh public key for the :code:`git-mirroring` user:

      .. code:: bash

        cat ~/.ssh/id_rsa.pub

   #) Clone the upstream repo:

      .. code:: bash

        git clone --mirror "$UPSTREAM_URL" ~/"$NAME".git

   #) Switch to the directory where you just cloned the repo:

      .. code:: bash

        cd ~/"$NAME".git

   #) Add the mirror as a new remote to allow pushing to it:

      .. code:: bash

        git remote add --mirror=push gitlab "$MIRROR_URL"

   #) Try pushing to the new remote to ensure everything is operating correctly:

      .. code:: bash

        git push gitlab

#) Switch back to the home directory:

   .. code:: bash

     cd

#) Ensure :code:`sync.sh` works properly:

   .. code:: bash

     ./sync.sh

#) Set up the cron job for running :code:`sync.sh`:

   a) Edit the user's :code:`crontab`:

      .. code:: bash

        crontab -u git-mirroring -e

   #) Add the following line to the end, then save and exit:

      .. code::

        * * * * * exec ~/sync.sh >> ~/sync.log 2>&1

#) Wait for the cron job to run (2 minutes should be sufficient), then check the log file:

   .. code:: bash

     less ~/sync.log

   The log file should exist and be empty, if it isn't empty, it contains error messages. If it doesn't exist, the cron job didn't run yet for some reason, try waiting a little longer.

#) Try pushing a commit to one of the upstream repos and seeing if it gets properly synced to the corresponding mirror repo. The sync job runs every minute, so wait 2 minutes and check.
