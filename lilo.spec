%define _enable_debug_packages %{nil}
%define debug_package %{nil}

%define _default_patch_fuzz 2

Summary:	The boot loader for Linux and other operating systems
Name:		lilo
Version:	24.0
Release:	2
Epoch:		1
License:	MIT
Group:		System/Kernel and hardware
Url:		https://lilo.alioth.debian.org/
Source0:	http://lilo.alioth.debian.org/ftp/sources/%{name}-%{version}.tar.gz
Source1:	rosa_256c.uu
Source2:	rosa_256c.dat
Patch0:		lilo-21.6-keytab-3mdk.patch
Patch1:		lilo-disks-without-partitions.patch
Patch2:		lilo-23.2.syslinux.patch
Patch9:		lilo-22.5.1-unsafe-and-default-table.patch
Patch26:	lilo-22.5.9-longer_image_names.patch
# [Pixel] the following patch was introduced in 2004 by Juan Quintela,
# it may be needed by longer_image_names patch above, but it seems unneeded
Patch27:	lilo-two_columns.patch
Patch28:	lilo-22.5.9-never-relocate-when-has-partititions.patch
Patch29:	lilo-22.5.9-initialize-Volume-IDs-with-no-fanfare.patch
Patch31:	lilo-exit_code_1_when_aborting.patch
Patch32:	lilo-22.6.1-turn-non-valid-boot-signature-into-a-warning.patch
Patch35:	lilo-22.6.1-large-memory-option-by-default.patch
Patch36:	lilo-23.2-no-debian.patch
Patch37:	lilo-24.0-Fix-make-install-when-lilo.static-is-not-built.patch
BuildRequires:	texlive
BuildRequires:	dev86
BuildRequires:	dev86-devel
BuildRequires:	nasm
BuildRequires:	device-mapper-devel
BuildRequires:	sharutils
Requires(post):	perl-base
Provides:	bootloader
ExclusiveArch:	%{ix86} x86_64

%description
LILO (LInux LOader) is a basic system program which boots your Linux
system. LILO loads the Linux kernel from a floppy or a hard drive, boots
the kernel and passes control of the system to the kernel. LILO can also
boot other operating systems.

%files
%doc README* COPYING
/sbin/*
%{_bindir}/*
%{_mandir}/*/*
/boot/rosa.bmp

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
          echo "ERROR: unknown lilo scheme, it is DROPPED (please file a bug at http://bugs.rosalinux.ru/)"
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

#----------------------------------------------------------------------------

%package doc
Summary:	More doc for %{name}
Group:		System/Kernel and hardware

%description doc
cf %{name} package.

%files doc
%doc doc/*.pdf QuickInst

#----------------------------------------------------------------------------

%prep
%setup -q
%patch0 -p1
%patch1 -p1
%patch2 -p1
%patch9 -p1
%patch26 -p1 -b .images
%patch27 -p1 -b .two
%patch28 -p1
%patch29 -p1
%patch31 -p1 -b .exit_code
%patch32 -p1
%patch35 -p1
%patch36 -p1
%patch37 -p1

bzip2 -9 README*

cp -a %{SOURCE1} %{SOURCE2} images/

# disable diagnostic build (which would need beeing root)
perl -pi -e 's/^(diagnostic:).*/diagnostic:/' Makefile

%build
perl -p -i -e "s/-Wall -g/%{optflags}/" Makefile
make all
(cd doc
make -f Makefile.old CFLAGS="%{optflags} -DDEBUG"
dvipdfm -o User_Guide.pdf user.dvi
dvipdfm -o Technical_Guide.pdf tech.dvi
rm -f *.aux *.log *.toc)

%install
%makeinstall_std

install -d %{buildroot}%{_bindir}
mv %{buildroot}%{_sbindir}/* %{buildroot}%{_bindir}

rm -rf %{buildroot}%{_sysconfdir}/initramfs %{buildroot}%{_sysconfdir}/kernel %{buildroot}%{_sysconfdir}/lilo.conf_example

