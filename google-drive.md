# rclone and google drive

Moving data from an HPC machine to google drive imposes several loops. Here a workaround for machines that have a connection towards Internet (will not work on SuperMUC-NG):
* Install `rclone` (https://rclone.org/) on a thirdparty machine.
* Create a google client_id following these instructions: https://rclone.org/drive/#making-your-own-client-id
* Configure rclone on the thirdparty machine by running `rclone config`. This executes an question/answer-based config utility.
* Important: 
  * if the thirdparty machine is headless, do *not* follow the installation instructions relative to `autoconfigure`, they are obsolete and will drive you down a useless rabbit hole. Answer `n` to the `autonconfigure` question and cut and past the link that the configuration utility gives you in your browser and proceed to authenticate the application with the gmail credentials that you have used to share the google-drive COVID space.
  * SA = Service Account in google lingo. Do not use it, it will give you a different google drive space than the one of your usual account. 

Installation and configuration steps:
* Install on your thirdparty machine. If you use two.radical-project this is already done
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
  * This is the name of the remote endpoint you will use in commands like `rclose ls <name_remote_endpoint>:`. Enter `gdrive` or whatever you prefer:
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
  * Create your content ID following the instructions or use the ID you have already created. The default is the credential used by rclone and likely the one already used by thousands of people. This will make `rclone` very slow so *use your own*:
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
  * IMPORTANT: Enter `n` if the thirdparty machine is headless:
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
* If it works, mount your rclone google-drive endpoint via FUSE on a folder in your home directory and put it in background as it does not return. Note you have to use `--drive-shared-with-me` otherwise you will not see the files/folders of the `shared with me` section of your google drive.
  ```
  mkdir ~/gdrive
  rclone --drive-shared-with-me mount gdrive: gdrive &
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

