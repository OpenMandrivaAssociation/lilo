%define _default_patch_fuzz 2

%define version 22.8
%define release %mkrel 4

Summary: The boot loader for Linux and other operating systems
Name: lilo
Version: %{version}
Release: %{release}
Epoch: 1
License: MIT
Group: System/Kernel and hardware
URL: http://lilo.go.dyndns.org/
Source: http://home.san.rr.com/johninsd/pub/linux/lilo/lilo-%{version}.tar.gz
#Source: ftp://lrcftp.epfl.ch/pub/linux/local/lilo/
Patch0: lilo-21.6-keytab-3mdk.patch
Patch1: lilo-disks-without-partitions.patch
Patch9: lilo-22.5.1-unsafe-and-default-table.patch
Patch22: lilo-22.8-mandir.patch
Patch26: lilo-22.5.9-longer_image_names.patch
# [Pixel] the following patch was introduced in 2004 by Juan Quintela, 
# it may be needed by longer_image_names patch above, but it seems unneeded
Patch27: lilo-two_columns.patch
Patch28: lilo-22.5.9-never-relocate-when-has-partititions.patch
Patch29: lilo-22.5.9-initialize-Volume-IDs-with-no-fanfare.patch
Patch31: lilo-exit_code_1_when_aborting.patch
Patch32: lilo-22.6.1-turn-non-valid-boot-signature-into-a-warning.patch
Patch33: lilo-22.6.1-cdrecord-is-wodim--mkisofs-is-genisoimage.patch
Patch35: lilo-22.6.1-large-memory-option-by-default.patch
BuildRequires: tetex-latex tetex-dvips tetex-dvipdfm dev86 dev86-devel nasm
BuildRequires: device-mapper-devel
Requires(post): perl-base
Provides: bootloader
Conflicts: lilo-doc < 22.5.7.2-6mdk
Exclusivearch: %{ix86} x86_64
Buildroot: %{_tmppath}/lilo-root

%package doc
Summary: More doc for %{name}
Group: System/Kernel and hardware
Conflicts: lilo < 22.5.7.2-6mdk

%description
LILO (LInux LOader) is a basic system program which boots your Linux
system.  LILO loads the Linux kernel from a floppy or a hard drive, boots
the kernel and passes control of the system to the kernel.  LILO can also
boot other operating systems.

%description doc
cf %{name} package

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch9 -p1
%patch22 -p1 -b .mandir
%patch26 -p1 -b .images
%patch27 -p1 -b .two
%patch28 -p1
%patch29 -p1
%patch31 -p1 -b .exit_code
%patch32 -p1
%patch33 -p1
%patch35 -p1

bzip2 -9 README*

# disable diagnostic build (which would need beeing root)
perl -pi -e 's/^(diagnostic:).*/diagnostic:/' Makefile

%build
perl -p -i -e "s/-Wall -g/$RPM_OPT_FLAGS/" Makefile
make
(cd doc
make CFLAGS="$RPM_OPT_FLAGS -DDEBUG"
dvipdfm -o User_Guide.pdf user.dvi
dvipdfm -o Technical_Guide.pdf tech.dvi
rm -f *.aux *.log *.toc)

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT%{_bindir}
make install ROOT=$RPM_BUILD_ROOT

rm $RPM_BUILD_ROOT/boot/diag1.img
mv $RPM_BUILD_ROOT/usr/sbin/* $RPM_BUILD_ROOT%{_bindir}

mkdir -p %buildroot/%{_mandir}/man{5,8}/
install -m644 manPages/*.5 %buildroot/%{_mandir}/man5/
install -m644 manPages/*.8 %buildroot/%{_mandir}/man8/

%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ -f /etc/lilo.conf ]; then

  if [ -L /boot/lilo ]; then

      # upgrading from old lilo boot.b based

      # before:
      # - message is a symlink to either lilo-text/message, lilo-menu/message or lilo-graphic/message
      # - lilo-text/message and lilo-menu/message are created by DrakX (and are usually the same file)
      # - lilo-graphic/message is in the RPM (will be removed by RPM after %post)
      # after:
      # - message-text is the text message
      # - message-graphic is the old lilo-graphic/message

      # transforming the /boot/message symlink in non-symlink
      if [ -e /boot/lilo-text/message ]; then
	  mv -f /boot/lilo-text/message /boot/message-text
      fi 
      if [ -e /boot/lilo-menu/message ]; then
	  mv -f /boot/lilo-menu/message /boot/message-text
      fi

      if [ -e /boot/message-text ]; then
          ln -sf message-text /boot/message
      fi

      # ensuring the right choice is taken

      link=`perl -e 'print readlink("/boot/lilo")'`
      case $link in
        lilo-menu) ;; # chosen by default
        lilo-bmp) ;; # automatically chosen by lilo based on "bitmap=..."
        lilo-graphic) ;; # obsolete
        lilo-text)
          # need a special install=... 
  	  perl -pi -e 's|^install=.*\n||; $_ = "install=text\n$_" if $. == 1' /etc/lilo.conf ;;
        *)
	  echo "ERROR: unknown lilo scheme, it is DROPPED (please tell pixel@mandriva.com)"
	  sleep 1 ;;
      esac

      rm -f /boot/lilo
  elif [ -e /boot/message-graphic ]; then
      if perl -e 'exit(-s "/boot/message" > 65_000 ? 0 : 1)'; then
      	 link=`perl -e 'print readlink("/boot/message")'`
	 rm /boot/message
	 if [ "$link" = "message-graphic" -a -e /boot/message-text ]; then
	   ln -s message-text /boot/message
	   if perl -e 'exit(-s "/boot/message" > 65_000 ? 0 : 1)'; then
 	     # weird message-text file... well someone had this on cooker, better be safe
	     echo > /boot/message
           fi
         else
	   echo > /boot/message
         fi
      fi      	 
  fi

  chmod 600 /etc/lilo.conf
  if [ -x /usr/sbin/detectloader ]; then
    LOADER=$(/usr/sbin/detectloader -q)
    if [ "$LOADER" = "LILO" ]; then
      /sbin/lilo > /dev/null
    fi
  fi
fi

%files
%defattr(-,root,root)
%doc README* COPYING
/sbin/*
%{_bindir}/*
%{_mandir}/*/*

%files doc
%defattr(-,root,root)
%doc doc/*.pdf CHANGES INCOMPAT QuickInst


