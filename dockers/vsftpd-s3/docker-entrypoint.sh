#!/bin/bash
set -euo pipefail
set -o errexit

trap 'kill -SIGQUIT $PID' INT

# VSFTPD PASV configuration
PASV_ADDRESS=${PASV_ADDRESS:-$(wget -qO- http://169.254.169.254/latest/meta-data/public-ipv4)}
PASV_MIN_PORT=${PASV_MIN_PORT:-65000}
PASV_MAX_PORT=${PASV_MAX_PORT:-65000}

# FTP allowed commands
# full command list : https://blog.vigilcode.com/2011/08/configure-secure-ftp-with-vsftpd/
CMDS_ALLOWED=${CMDS_ALLOWED:-EPSV,EPRT,ABOR,ALLO,APPE,CCC,CDUP,CWD,DELE,FEAT,HELP,LIST,LPSV,MKD,MLST,MODE,NLST,NOOP,OPTS,PASS,PASV,PBSZ,PORT,PWD,QUIT,REIN,REST,RETR,RMD,RNFR,RNTO,SITE,SIZE,STAT,STOR,STRU,SYST,TYPE,USER}

# Configure vsftpd
mkdir -p /var/run/vsftpd/empty
echo "listen=YES
anonymous_enable=NO
local_enable=YES
write_enable=YES
log_ftp_protocol=YES
chroot_local_user=YES
allow_writeable_chroot=YES
delete_failed_uploads=YES
port_enable=YES
port_promiscuous=YES
cmds_allowed=$CMDS_ALLOWED
pasv_enable=YES
pasv_promiscuous=YES
pasv_min_port=$PASV_MIN_PORT
pasv_max_port=$PASV_MAX_PORT" > /etc/vsftpd.conf
[ -n "$PASV_ADDRESS" ] && echo "pasv_address=$PASV_ADDRESS" >> /etc/vsftpd.conf


# Amazon S3 bucket
S3_ACL=${S3_ACL:-private}
S3_BUCKET=${S3_BUCKET:-s3bucket}

# Amazon credentials
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID:-aws_access_key_id}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY:-aws_secret_access_key}

# VSFTPD credentials
FTPD_USER=${FTPD_USER:-s3ftp}
FTPD_PASS=${FTPD_PASS:-s3ftp}

# Create FTP user
adduser --home /home/${FTPD_USER} --disabled-login ${FTPD_USER} --gecos ""
echo "${FTPD_USER}:${FTPD_PASS:-$FTPD_PASS}" | chpasswd 2> /dev/null

chown -R ${FTPD_USER} /home/${FTPD_USER}
chmod -R 777 /home/${FTPD_USER}

# Configure s3fs
echo "${aws_access_key_id:-$AWS_ACCESS_KEY_ID}:${aws_secret_access_key:-$AWS_SECRET_ACCESS_KEY}" > /etc/passwd-s3fs
chmod 600 /etc/passwd-s3fs

# Mount s3fs
s3fs ${s3_bucket:-$S3_BUCKET} /home/${FTPD_USER} -o nosuid,nonempty,no_check_certificate,nodev,allow_other,complement_stat,mp_umask=027,uid=$(id -u ${FTPD_USER}),gid=$(id -g ${FTPD_USER}),passwd_file=/etc/passwd-s3fs,default_acl=${S3_ACL},retries=5

# Launch vsftpd
vsftpd /etc/vsftpd.conf
