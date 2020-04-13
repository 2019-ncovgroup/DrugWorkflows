# rclone and google drive

Moving data between HPC machines and Google Drive imposes several hops:
* Install `rclone` (https://rclone.org/) on a third party machine.
* Create a google client_id following these instructions: https://rclone.org/drive/#making-your-own-client-id
* Configure rclone on the third party machine by running `rclone config`.
* Important: 
  * if the third party machine is headless, do *not* follow the installation instructions relative to `autoconfigure` on the rclone website, they are obsolete and will lead you down a useless rabbit hole. See instructions below instead.
  * SA = Service Account in google lingo. Do not use it, it will give you a different google drive space than the one of your usual account. 

Installation and configuration steps:
* Install on your third party machine (already done on two.radical-project):
  ```
  curl https://rclone.org/install.sh | sudo bash
  ```
* Configure a remote endpoint:
  ```
  rclone config
  ```
  * Enter `n`:
    ```
    No remotes found - make a new one
    n) New remote
    s) Set configuration password
    q) Quit config
    n/s/q>
    ```
  * This is the name of the remote endpoint you will use in commands like `rclone ls <name_remote_endpoint>:`. Enter `gdrive` or whatever you prefer:
    ```
    name>
    ```
  * Enter `13`:
    ```
    Type of storage to configure.
    Enter a string value. Press Enter for the default ("").
    Choose a number from below, or type in your own value
    [...]
    12 / Google Cloud Storage (this is not Google Drive)
       \ "google cloud storage"
    13 / Google Drive
       \ "drive"
    14 / Google Photos
       \ "google photos"
    [...]
    ```
  * Create your content ID following the instructions. The default is the credential used by rclone and likely the one already used by thousands of people. This will make `rclone` very slow so *use your own*:
    ```
    ** See help for drive backend at: https://rclone.org/drive/ **
    
    Google Application Client Id
    Setting your own is recommended.
    See https://rclone.org/drive/#making-your-own-client-id for how to create your own.
    If you leave this blank, it will use an internal key which is low performance.
    Enter a string value. Press Enter for the default ("").
    client_id>
    ```
  * Enter the "secret" associated to your client ID:
    ```
    Google Application Client Secret
    Setting your own is recommended.
    Enter a string value. Press Enter for the default ("").
    client_secret>
    ```
  * Enter `1`:
    ```
    Scope that rclone should use when requesting access from drive.
    Enter a string value. Press Enter for the default ("").
    Choose a number from below, or type in your own value
    1 / Full access all files, excluding Application Data Folder.
      \ "drive"
    2 / Read-only access to file metadata and file contents.
      \ "drive.readonly"
    [...]
    ```
  * Leave blank:
    ```
    ID of the root folder
    Leave blank normally.
    
    Fill in to access "Computers" folders (see docs), or for rclone to use
    a non root folder as its starting point.
    
    Note that if this is blank, the first time rclone runs it will fill it
    in with the ID of the root folder.
    
    Enter a string value. Press Enter for the default ("").
    root_folder_id> 
    ```
  * Leave blank:
    ```
    Service Account Credentials JSON file path 
    Leave blank normally.
    Needed only if you want use SA instead of interactive login.
    Enter a string value. Press Enter for the default ("").
    service_account_file>
    ```
  * Accept default:
    ```
    Edit advanced config? (y/n)
    y) Yes
    n) No (default)
    y/n> 
    ```
  * IMPORTANT: Enter `n` if the third party machine is headless:
    ```
    Remote config
    Use auto config?
     * Say Y if not sure
     * Say N if you are working on a remote or headless machine
    y) Yes (default)
    n) No
    y/n>
    ```
    Once you entered `n`, the following will be printed:
    ```
    Please go to the following link: https://accounts.google.com/o/oauth2/auth?access_type=offline&client_id=<LONG_ID>
    Log in and authorize rclone for access
    ```
    Cut & paste (C&P) that address into your browser and authenticate with the identity associated to the email address you provided to access the google drive space of your workflow. This returns a verification code in your browser.
  * Enter your verification code:
    ```
    Enter verification code> 
    ```
  * Accept default:
    ```
    Configure this as a team drive?
    y) Yes
    n) No (default)
    y/n>
    ```
  * Accepts default:
    ```
    --------------------
    [gdrive]
    type = drive
    client_id = <CLIENT_ID>
    client_secret = <CLIENT_SECRET>
    scope = drive
    token = {"access_token":"<TOKEN>","expiry":"<DATE>"}
    --------------------
    y) Yes this is OK (default)
    e) Edit this remote
    d) Delete this remote
    y/e/d>
    ```
  * Enter `q` and you are done.
    ```
    Current remotes:

    Name                 Type
    ====                 ====
    gdrive               drive
    
    e) Edit existing remote
    n) New remote
    d) Delete remote
    r) Rename remote
    c) Copy remote
    s) Set configuration password
    q) Quit config
    e/n/d/r/c/s/q> q
    ```
* Test your endpoint with:
  ```
  rclone ls gdrive:
  ```
* If it works, mount your rclone google drive endpoint via FUSE on a folder in your home directory and put it in background. Note you have to use `--drive-shared-with-me` otherwise you will not see the files/folders of the `shared with me` section of your google drive. If you want to be able to seek files opened for write and open files for both read AND write (i.e., overwrite existing files), use also `--vfs-cache-mode writes`:
  ```
  mkdir ~/gdrive
  rclone --drive-shared-with-me mount gdrive: gdrive &
  ```
  If you want to be able to seek files opened for write and open files for both read AND write (i.e., overwrite existing files), use also `--vfs-cache-mode writes` (see https://rclone.org/commands/rclone_mount/#file-caching). This will make google drive behave more like a filesystem but do not expect the reliability of a real file system:
  ```
  rclone --drive-shared-with-me mount gdrive: gdrive --vfs-cache-mode writes
  ```
  If you want to demonize `rclone mount` you can use `--deamon` or systemd (see https://github.com/rclone/rclone/wiki/rclone-fstab-mount-helper-script#systemd):
  ```
  rclone --drive-shared-with-me mount gdrive: gdrive --vfs-cache-mode writes --daemon
  ```
* Test the mount by listing the directory in which you mounted run rclone remote endpoint. NOTE: files and folders of the `shared with me` section are available in the root of your remote mount point, not under a dedicated folder.
  ```
  cd ~/gdrive
  ls 
  ```
* If all this worked, now. you can use `ssh` and `scp` to issues commands from the HPC resource to the google drive, and to upload/download files from the HPC machine to the google drive of your workflow. For example:
  ```
  ssh mturilli@two.radical-project.org mkdir /home/mturilli/gdrive/Workflow0COVID/results/2
  scp Mpro-x*-receptor.* mturilli@two.radical-project.org:/home/mturilli/gdrive/Workflow0COVID/results/2/
  ```

