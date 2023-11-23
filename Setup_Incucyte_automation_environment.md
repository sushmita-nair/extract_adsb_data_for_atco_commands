# Set up Incucyte automation environment

Steps to set up data management/transfer automation environment on Incucyte microscope controller:

1. Check execution policy: `Get-ExecutionPolicy`
    
    If execution policy is `Restricted`:
    
    Change execution policy to `RemoteSigned` for cidas (the default for windows client is Restricted see here: [https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.4](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_execution_policies?view=powershell-7.4) ):
    
    `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
    
2. Download and install Git (64 bit Standalone) from here: [https://git-scm.com/download/win](https://git-scm.com/download/win)
3. Edit environment variable (user variable for cidas) : add `C:\Program Files\Git\usr\bin` to `Path` 
4. Create ssh keys and upload public key to your git:
    
    `ssh-keygen`
    
5. Add public key to your GitHub account : [https://github.com/settings/keys](https://github.com/settings/keys) under name `ssh_cidas_sX`
6. Clone incucyte automation repo into cidas\Documents: [https://github.com/computational-cell-analytics/incucyte-automation](https://github.com/computational-cell-analytics/incucyte-automation)
7. Install Micromamba: [https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html](https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html)
    1. `Invoke-Webrequest -URI https**://**micro**.**mamba**.**pm**/**api**/**micromamba**/**win****64**/**latest -OutFile micromamba**.**tar**.**bz2`
        
        If error: *“Could not create SSL/TSL secure channel”*
        
        Might need to change TSL version by:
        
        `[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12`
        
    2. Unzip using: `tar xf micromamba**.**tar**.**bz2`
    3. Get exe file:`MOVE -Force Library**\**bin**\**micromamba**.**exe micromamba**.**exe`
    4. **`.\**micromamba**.**exe ****help`
    5. Set root prefix`$Env:MAMBA_ROOT_PREFIX**=**"C:Users\Cidas\micromamba\”`
    6. Invoke the hook**`.\**micromamba**.**exe shell hook -s powershell **|** Out-String **|** Invoke-Expression`
    7. OR, Initialize the shell**`.\**micromamba**.**exe shell init -s powershell -p C:Users\Cidas\micromamba\`
    8. Create micromamba env using python 3.11. Python 3.12 isn’t compatible since #1 in
        
        [Tracking issues](https://www.notion.so/Tracking-issues-a83274b2f1bd4c3ca4e00a05f7ce21b4?pvs=21)
        
         `micromamba create -n data_mgm **f** C:Users\Cidas\Documents\incucyte-automation\enviroment.yaml python=3.11`
        
    9. Activate the env`micromamba activate data_mgm`
8. Download VS Code: [https://code.visualstudio.com/download](https://code.visualstudio.com/download)
    
    Add to `Path`(user variable): `C:\Program Files\Microsoft VS Code\bin`
    
    Sign-in to VS code using Github if needed