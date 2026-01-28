# EC2 SSH Connection Troubleshooting

## Current Status
- **EC2 IP**: 16.170.104.186
- **Instance ID**: i-035811fd86b8a4974
- **Key Pair**: keys-mhcl
- **Key File**: C:\Users\user\Desktop\mhcl\keys-mhcl.pem
- **Issue**: Permission denied (publickey)

## Steps to Verify

### 1. Check EC2 Instance Details in AWS Console
1. Go to EC2 Dashboard → Instances
2. Select instance `i-035811fd86b8a4974`
3. Check **Details** tab:
   - **Key pair assigned at launch**: Should be "keys-mhcl"
   - **AMI ID**: Note the AMI (determines default username)
   - **Platform**: Should be Ubuntu

### 2. Verify Key Pair Match
1. Go to EC2 → Key Pairs
2. Find "keys-mhcl"
3. Check **Fingerprint**: `d51ba4b-b2-9c-9-0a-a7-0b-2f-e4-69-55e-1-52-0...`
4. This should match the key file you downloaded

### 3. Common Default Usernames by AMI
- **Ubuntu AMI**: `ubuntu`
- **Amazon Linux 2**: `ec2-user`
- **Amazon Linux 2023**: `ec2-user`
- **Debian**: `admin`
- **RHEL**: `ec2-user`
- **SUSE**: `ec2-user`

### 4. Check if Instance is Running
```powershell
# Test if instance is reachable
Test-NetConnection -ComputerName 16.170.104.186 -Port 22
```

### 5. Verify Security Group
1. Go to EC2 → Security Groups
2. Find the security group attached to your instance
3. Check **Inbound rules**:
   - Should have: Type=SSH, Port=22, Source=Your IP or 0.0.0.0/0

## Possible Solutions

### Solution 1: Re-download Key Pair
If you downloaded the key after instance creation, it won't work. You need to:
1. Stop the instance
2. Detach root volume
3. Attach to another instance
4. Modify authorized_keys
5. Reattach and start

### Solution 2: Use EC2 Instance Connect
1. Go to EC2 Console
2. Select your instance
3. Click **Connect** → **EC2 Instance Connect**
4. This gives you browser-based SSH access

### Solution 3: Use Session Manager (if SSM agent installed)
1. Go to Systems Manager → Session Manager
2. Start session with your instance
3. No SSH key needed

### Solution 4: Create New Instance with Correct Key
If the key truly doesn't match, easiest is to:
1. Create AMI from current instance
2. Launch new instance from AMI with correct key pair

## Next Steps

**Please check in AWS Console:**
1. What AMI is the instance using? (Ubuntu 20.04, 22.04, Amazon Linux, etc.)
2. Is "keys-mhcl" definitely assigned to instance i-035811fd86b8a4974?
3. Can you access via EC2 Instance Connect?

**Then we can:**
- Try the correct username for your AMI
- Or use EC2 Instance Connect to add your key manually
- Or proceed with deployment using Session Manager
