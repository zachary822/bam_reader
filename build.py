from Cython.Build import cythonize, build_ext


def build(setup_kwargs):
    setup_kwargs.update(
        {
            "ext_modules": cythonize(
                "bam_reader/*.pyx",
                language_level=3,
            ),
            "cmdclass": {"build_ext": build_ext},
        }
    )
