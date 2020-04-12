# Workflow-0 Campaign

Logs and results have been moved to google drive. Moving data from an HPC machine to google drive imposes several loops. Here a workaround for machines that have a connection towards Internet (will not work on SuperMUC-NG):
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




## Enamine_REAL_diversity_set_15.5M.smi - ADRP-ADPR_pocket1_receptor.oeb - HR - rerun with new code

- oebs: https://anl.box.com/s/zw7euszrfkmi4hhp2ao5upaf58bb0ina
- Results: https://github.com/2019-ncovgroup/DrugWorkflows/tree/devel/workflow-0/results/enamine_real_diversity_set_db-2-1

| OEB                               | Machine  | Assignee | State   | Missing |
|-----------------------------------|----------|----------|---------|---------|
| ADRP-ADPR_pocket1_receptor.oeb    | Frontera | MT       | Running |         |


## discovery_set_db.smi - Fourth set of receptors - HR - rerun with new code

- oebs: https://anl.app.box.com/s/m9aw6c7lfv6kv2eshgoaj6jphtc8vyz1
- Results: https://github.com/2019-ncovgroup/workflow-0-results/tree/master/discovery_set_db-4-1

| OEB                             | Machine  | Assignee | State   | Missing |
|---------------------------------|----------|----------|---------|---------|
| 3CLPro_pocket1_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket1_receptor.oeb       | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket3_receptor.oeb       | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket6_receptor.oeb       | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket8_receptor.oeb       | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket9_receptor.oeb       | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket11_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket13_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket17_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket18_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket22_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket23_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket37_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket57_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket62_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket71_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket100_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket108_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket130_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket135_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket143_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket154_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket156_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket157_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| ADRP_ADPR_pocket1_receptor.oeb  | Frontera | MT       | Done    |  0.1%   |
| ADRP-ADPR_pocket5_receptor.oeb  | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_receptor.oeb       | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket12_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket13_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| CoV_pocket1_receptor.oeb        | Frontera | MT       | Done    |  0.1%   |
| CoV_pocket2_receptor.oeb        | Frontera | MT       | Done    |  0.1%   |
| CoV_pocket8_receptor.oeb        | Frontera | MT       | Done    |  0.1%   |
| CoV_pocket10_receptor.oeb       | Frontera | MT       | Done    |  0.1%   |
| Nsp10_pocket1_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| Nsp10_pocket3_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| Nsp10_pocket26_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| nsp15-CIT_pocket1_receptor.oeb  | Frontera | MT       | Done    |  0.1%   |
| nsp15-CIT_pocket6_receptor.oeb  | Frontera | MT       | Done    |  0.1%   |
| nsp15-CIT_pocket13_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| nsp15-CIT_pocket18_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| nsp15-CIT_pocket37_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| nsp15_pocket1_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| nsp15_pocket2_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| nsp15_pocket13_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| nsp15_pocket14_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| nsp15_pocket29_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| nsp15_pocket33_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| nsp15_pocket36_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| Nsp9_pocket2_receptor.oeb       | Frontera | MT       | Done    |  0.1%   |
| Nsp9_pocket7_receptor.oeb       | Frontera | MT       | Done    |  0.1%   |
| orf7a_pocket2_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| PLPro_pocket1_receptor.oeb      | Frontera | MT       | Missing |         |
| PLPro_pocket3_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| PLPro_pocket4_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| PLPro_pocket6_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| PLPro_pocket23_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| PLPro_pocket50_receptor.oeb     | Frontera | MT       | Done    |  9  %   |

## Enamine_REAL_diversity_set_15.5M.smi - ADRP-ADPR_pocket1_receptor.oeb - HR

- oebs: https://anl.box.com/s/zw7euszrfkmi4hhp2ao5upaf58bb0ina
- Results: https://github.com/2019-ncovgroup/DrugWorkflows/tree/devel/workflow-0/results/enamine_real_diversity_set_db-2

| OEB                               | Machine  | Assignee | State   | Missing |
|-----------------------------------|----------|----------|---------|---------|
| ADRP-ADPR_pocket1_receptor.oeb    | Frontera | MT       | Done    | 1.3%    |

## discovery_set_db.smi - Fourth set of receptors - HR

- oebs: https://anl.box.com/s/zw7euszrfkmi4hhp2ao5upaf58bb0ina
- Results: https://github.com/2019-ncovgroup/DrugWorkflows/tree/devel/workflow-0/results/discovery_set_db-4

| OEB                            | Machine  | Assignee | State   | Missing |
|--------------------------------|----------|----------|---------|---------|
| 3CLPro_pocket1_receptor.oeb    | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket100_receptor.oeb    | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket108_receptor.oeb    | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket11_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket130_receptor.oeb    | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket135_receptor.oeb    | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket13_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket143_receptor.oeb    | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket154_receptor.oeb    | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket156_receptor.oeb    | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket157_receptor.oeb    | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket17_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket18_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket1_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket22_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket23_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket37_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket3_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket57_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket62_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket6_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket71_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket8_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| 6vww_pocket9_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| ADRP-ADPR_pocket1_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP-ADPR_pocket5_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket12_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket13_receptor.oeb     | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| CoV_pocket10_receptor.oeb      | Frontera | MT       | Done    |  0.1%   |
| CoV_pocket1_receptor.oeb       | Frontera | MT       | Done    |  0.1%   |
| CoV_pocket2_receptor.oeb       | Frontera | AA       | Done    |  0.1%   |
| CoV_pocket8_receptor.oeb       | Frontera | AA       | Done    |  0.1%   |
| Nsp10_pocket1_receptor.oeb     | Frontera | AA       | Done    |  0.1%   |
| Nsp10_pocket26_receptor.oeb    | Frontera | AA       | Done    |  0.1%   |
| Nsp10_pocket3_receptor.oeb     | Frontera | AA       | Done    |  0.1%   |
| nsp15-CIT_pocket13_receptor.oeb| Frontera | AA       | Done    |  0.1%   |
| nsp15-CIT_pocket18_receptor.oeb| Frontera | AA       | Done    |  0.1%   |
| nsp15-CIT_pocket1_receptor.oeb | Frontera | AA       | Done    |  0.1%   |
| nsp15-CIT_pocket37_receptor.oeb| Frontera | AA       | Done    |  0.1%   |
| nsp15-CIT_pocket6_receptor.oeb | Frontera | AA       | Done    |  0.1%   |
| nsp15_pocket13_receptor.oeb    | Frontera | AA       | Done    |  0.1%   |
| nsp15_pocket14_receptor.oeb    | Frontera | AA       | Done    |  0.1%   |
| nsp15_pocket1_receptor.oeb     | Frontera | AA       | Done    |  0.1%   |
| nsp15_pocket29_receptor.oeb    | Frontera | AA       | Done    |  0.1%   |
| nsp15_pocket2_receptor.oeb     | Frontera | AA       | Done    |  0.1%   |
| nsp15_pocket33_receptor.oeb    | Frontera | AA       | Done    |  0.1%   |
| nsp15_pocket36_receptor.oeb    | Frontera | AA       | Done    |  0.1%   |
| Nsp9_pocket2_receptor.oeb      | Frontera | AA       | Done    |  0.1%   |
| Nsp9_pocket7_receptor.oeb      | Frontera | AA       | Done    |  0.1%   |
| orf7a_pocket2_receptor.oeb     | Frontera | AA       | Done    |  0.1%   |
| PLPro_pocket23_receptor.oeb    | Frontera | AA       | Done    |  0.1%   |
| PLPro_pocket3_receptor.oeb     | Frontera | AA       | Done    |  0.1%   |
| PLPro_pocket4_receptor.oeb     | Frontera | AA       | Done    |  0.1%   |
| PLPro_pocket50_receptor.oeb    | Frontera | AA       | Done    |  14.1%  |
| PLPro_pocket6_receptor.oeb     | Frontera | AA       | Done    |  0.1%   |

## discovery_set_db.smi - Third set of receptors

- oebs: https://anl.app.box.com/s/vo733ejfref9g8pskzx9lkqs25951hn1
- Results: https://github.com/2019-ncovgroup/DrugWorkflows/tree/devel/workflow-0/results/discovery_set_db-3

| OEB                | Machine  | Assignee | State   | Missing |
|--------------------|----------|----------|---------|---------|
| Mpro-x0104.pdb.oeb | Frontera | AA       | Done    |  0.1%   |
| Mpro-x0354.pdb.oeb | Frontera | AA       | Done    |  0.1%   |
| Mpro-x0072.pdb.oeb | Frontera | AA       | Done    |  0.1%   |
| Mpro-x0305.pdb.oeb | Frontera | AA       | Done    |  0.1%   |
| Mpro-x0195.pdb.oeb | Frontera | AA       | Done    |  0.1%   |
| Mpro-x0387.pdb.oeb | Frontera | AA       | Done    |  0.1%   |
| Mpro-x0107.pdb.oeb | Frontera | AA       | Done    |  0.1%   |
| Mpro-x0161.pdb.oeb | Frontera | AA       | Done    |  0.1%   |
| Mpro-x0395.pdb.oeb | Frontera | AA       | Done    |  0.1%   |
| Mpro-x0397.pdb.oeb | Frontera | AA       | Done    |  0.1%   |
| Mpro-x0426.pdb.oeb | Frontera | AA       | Done    |  0.1%   |
| Mpro-x0434.pdb.oeb | Frontera | MT       | Done    |  0.1%   |
| Mpro-x0540.pdb.oeb | Frontera | MT       | Done    |  0.1%   |
| Mpro-x0678.pdb.oeb | Frontera | MT       | Done    |  0.1%   |
| Mpro-x0874.pdb.oeb | Frontera | MT       | Done    |  0.1%   |
| Mpro-x0946.pdb.oeb | Frontera | MT       | Done    |  0.1%   |
| Mpro-x0967.pdb.oeb | Frontera | MT       | Done    |  0.1%   |
| Mpro-x0991.pdb.oeb | Frontera | MT       | Done    |  0.1%   |
| Mpro-x0995.pdb.oeb | Frontera | MT       | Done    |  0.1%   |
| Mpro-x1077.pdb.oeb | Frontera | MT       | Done    |  0.1%   |
| Mpro-x1093.pdb.oeb | Frontera | MT       | Done    |  0.1%   |
| Mpro-x1249.pdb.oeb | Frontera | MT       | Done    |  0.1%   |

## discovery_set_db.smi - Second set of receptors

- oebs: https://anl.app.box.com/s/bn2v9thf266g0gav82l715mihhz4zutz
- Results: https://github.com/2019-ncovgroup/DrugWorkflows/tree/devel/workflow-0/results/discovery_set_db-2

| OEB                                            | Machine  | Assignee | State   | Missing |
|------------------------------------------------|----------|----------|---------|---------|
| ADRP_pocket1_rank1579_370_pocket1_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank1579_370_pocket2_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank1579_471_pocket1_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank1579_471_pocket6_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank1579_471_pocket7_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank1579_out_pocket1_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank2355_386_pocket4_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank2355_490_pocket3_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank2355_out_pocket1_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank2437_454_pocket4_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank2437_454_pocket7_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank2437_469_pocket1_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank2437_out_pocket3_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank2437_out_pocket5_receptor.oeb | Frontera | AA       | Done    |  0.1%   |
| ADRP_pocket1_rank2437_out_pocket8_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank941_152_pocket12_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank941_152_pocket4_receptor.oeb  | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank941_411_pocket2_receptor.oeb  | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank941_411_pocket3_receptor.oeb  | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank941_out_pocket8_receptor.oeb  | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank976_106_pocket1_receptor.oeb  | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank976_107_pocket1_receptor.oeb  | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank976_out_pocket13_receptor.oeb | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank976_out_pocket1_receptor.oeb  | Frontera | MT       | Done    |  0.1%   |
| ADRP_pocket1_rank976_out_pocket7_receptor.oeb  | Frontera | MT       | Done    |  0.1%   |

## Enamine_REAL_diversity_set_15.5M.smi - ADRP_pocket1_receptor.oeb

| OEB                             | Machine  | Assignee | State |
|---------------------------------|----------|----------|-------|
| Enamine_REAL_diversity_set__000 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__001 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__002 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__003 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__004 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__005 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__006 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__007 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__008 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__009 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__010 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__011 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__012 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__013 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__014 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__015 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__016 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__017 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__018 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__019 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__020 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__021 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__022 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__023 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__024 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__025 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__026 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__027 | Frontera | MT       | Done  | 
| Enamine_REAL_diversity_set__028 | Frontera | MT       | Done  | 

## discovery_set_db.smi - First set of receptors

- oebs: https://anl.app.box.com/s/m9aw6c7lfv6kv2eshgoaj6jphtc8vyz1
- Results: https://github.com/2019-ncovgroup/DrugWorkflows/tree/devel/workflow-0/results

| OEB                             | Machine  | Assignee | State   | Missing |
|---------------------------------|----------|----------|---------|---------|
| ADRP_pocket1_receptor.oeb       | Comet    | MT       | Done    |   0.1 % |
| ADRP_pocket12_receptor.oeb      | Frontera | MT       | Partial |  48.6 % |
| ADRP_pocket13_receptor.oeb      | Comet    | MT       | Done    |   9.0 % |
| Nsp10_pocket1_receptor.oeb      | Theta    | AM       | Done    |   1.6 % |
| Nsp10_pocket3_receptor.oeb      | Frontera | MT       | Done    |   0.1 % |
| Nsp10_pocket26_receptor.oeb     | Comet    | MT       | Done    |   0.1 % |
| nsp15-CIT_pocket1_receptor.oeb  | Theta    | AM       | Done    |   7.6 % |
| nsp15-CIT_pocket6_receptor.oeb  | Theta    | AM       | Done    |   4.3 % |
| nsp15-CIT_pocket13_receptor.oeb | Theta    | AM       | Done    |   0.1 % |
| nsp15-CIT_pocket18_receptor.oeb | Frontera | MT       | Done    |   2.0 % |
| nsp15-CIT_pocket37_receptor.oeb | Comet    | MT       | Done    |  13.2 % |
| PLPro_pocket3_receptor.oeb      | Frontera | MT       | Done    |   0.1 % |
| PLPro_pocket4_receptor.oeb      | Frontera | MT       | Done    |   0.1 % |
| PLPro_pocket6_receptor.oeb      | Frontera | MT       | Done    |   0.1 % |
| PLPro_pocket23_receptor.oeb     | Theta    | AM       | Done    |   0.1 % |
| CoV_pocket1_receptor.oeb        | Frontera | AM       | Done    |   3.5 % |
| CoV_pocket2_receptor.oeb        | Frontera | AM       | Done    |   5.4 % |
| CoV_pocket8_receptor.oeb        | Theta    | AM       | Done    |   3.9 % |
| CoV_pocket10_receptor.oeb       | Frontera | AM       | Partial |  67.9 % |

