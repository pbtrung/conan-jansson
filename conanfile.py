from conans import ConanFile, ConfigureEnvironment
import os
from conans.tools import download
from conans.tools import unzip, replace_in_file
from conans import CMake


class JanssonConan(ConanFile):
    description = "C library for encoding, decoding and manipulating JSON data"
    name = "jansson"
    version = "2.10"
    ZIP_FOLDER_NAME = "jansson-%s" % version
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False], "fPIC": [True, False]}
    default_options = "shared=False", "fPIC=True"
    url="http://github.com/pbtrung/conan-jansson"
    license="https://github.com/akheron/jansson/blob/v2.10/LICENSE"
    
    def config(self):
        try: # Try catch can be removed when conan 0.8 is released
            del self.settings.compiler.libcxx 
        except: 
            pass
        
        if self.settings.os == "Windows":
            self.options.remove("fPIC")
        
    def source(self):
        zip_name = "%s.tar.gz" % self.ZIP_FOLDER_NAME
        download("http://www.digip.org/jansson/releases/%s" % zip_name, zip_name)
        unzip(zip_name)
        os.unlink(zip_name)

    def build(self):
        """ Define your project building. You decide the way of building it
            to reuse it later in any other project.
        """
        env = ConfigureEnvironment(self.deps_cpp_info, self.settings)
        if self.settings.os == "Linux" or self.settings.os == "Macos":
            if self.options.fPIC:
                 env_line = env.command_line.replace('CFLAGS="', 'CFLAGS="-fPIC ')
            else:
                 env_line = env.command_line     
            if self.settings.os == "Macos":
                old_str = '-install_name \$rpath/\$soname'
                new_str = '-install_name \$soname'
                replace_in_file("./%s/configure" % self.ZIP_FOLDER_NAME, old_str, new_str)
                     
            configure = "cd %s && %s ./configure" % (self.ZIP_FOLDER_NAME, env_line)
            self.output.warn(configure)
            self.run(configure)
            self.run("cd %s && %s make" % (self.ZIP_FOLDER_NAME, env_line))
        else:
            conan_magic_lines = '''project(jansson)
    cmake_minimum_required(VERSION 3.0)
    include(../conanbuildinfo.cmake)
    CONAN_BASIC_SETUP()
    '''
            replace_in_file("%s/CMakeLists.txt" % self.ZIP_FOLDER_NAME, "cmake_minimum_required(VERSION 2.4.4)", conan_magic_lines)
            replace_in_file("%s/CMakeLists.txt" % self.ZIP_FOLDER_NAME, "project(jansson C)", "")
            
            if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio" and self.settings.compiler.version==14:
                replace_in_file("%s/CMakeLists.txt" % self.ZIP_FOLDER_NAME, "check_function_exists (snprintf HAVE_SNPRINTF)", "SET(HAVE_SNPRINTF 1)")
            
            cmake = CMake(self.settings)
            shared_options = "-DJANSSON_BUILD_SHARED_LIBS=ON" if self.options.shared else "-DJANSSON_BUILD_SHARED_LIBS=OFF"
            other_options = "-DJANSSON_BUILD_DOCS=OFF"
            if self.settings.os == "Windows" and self.settings.compiler == "Visual Studio":
                if str(self.settings.compiler.runtime) in ("MT", "MTd"):
                    other_options += " -DSTATIC_CRT=ON -DJANSSON_STATIC_CRT=ON"
                else:
                    other_options += " -DSTATIC_CRT=OFF -DJANSSON_STATIC_CRT=OFF"
                 
            self.run("cd %s && mkdir _build" % self.ZIP_FOLDER_NAME)
            cd_build = "cd %s/_build" % self.ZIP_FOLDER_NAME
            self.run('%s && cmake .. %s %s %s' % (cd_build, cmake.command_line, shared_options, other_options))
            self.run("%s && cmake --build . %s" % (cd_build, cmake.build_config))
                
    def package(self):
        """ Define your conan structure: headers, libs, bins and data. After building your
            project, this method is called to create a defined structure:
        """
        # Copying headers
        self.copy("*.h", "include", "%s" % (self.ZIP_FOLDER_NAME), keep_path=False)

        # Copying static and dynamic libs
        if self.settings.os == "Windows":
            if self.options.shared:
                self.copy(pattern="*.dll", dst="bin", src=self.ZIP_FOLDER_NAME, keep_path=False)
            self.copy(pattern="*.lib", dst="lib", src=self.ZIP_FOLDER_NAME, keep_path=False)
        else:
            if self.options.shared:
                if self.settings.os == "Macos":
                    self.copy(pattern="*.dylib", dst="lib", keep_path=False)
                else:
                    self.copy(pattern="*.so*", dst="lib", src=self.ZIP_FOLDER_NAME, keep_path=False)
            else:
                self.copy(pattern="*.a", dst="lib", src=self.ZIP_FOLDER_NAME, keep_path=False)

    def package_info(self):
        if self.settings.os == "Windows":
            self.cpp_info.libs = ['jansson']
            if self.settings.build_type == "Debug":
                self.cpp_info.libs[0] += "_d"
        else:
            self.cpp_info.libs = ['jansson']
