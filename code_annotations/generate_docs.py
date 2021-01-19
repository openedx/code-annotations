"""
Contains functionality for turning YAML reports into human-readable documentation.
"""

import collections
import datetime
import os

import jinja2
import yaml
from slugify import slugify


class ReportRenderer:
    """
    Generates human readable documentation from YAML reports.
    """

    def __init__(self, config, report_files):
        """
        Initialize a ReportRenderer.

        Args:
            config: An AnnotationConfig object
            report_files: A list of files to combine and report on
        """
        self.config = config
        self.echo = self.config.echo
        self.report_files = report_files
        self.create_time = datetime.datetime.now().isoformat()

        self.full_report = self._aggregate_reports()

        self.jinja_environment = jinja2.Environment(
            autoescape=False,
            loader=jinja2.FileSystemLoader(self.config.report_template_dir),
            lstrip_blocks=True,
            trim_blocks=True
        )
        self.top_level_template = self.jinja_environment.get_template('annotation_list.tpl')
        self.all_choices = []
        self.group_mapping = {}

        for token in self.config.choices:
            self.all_choices.extend(self.config.choices[token])

        for group_name in self.config.groups:
            for token in self.config.groups[group_name]:
                self.group_mapping[token] = group_name

    def _add_report_file_to_full_report(self, report_file, report):
        """
        Add a specified report file to a report.

        Args:
            report_file:
            report:

        Returns:

        """
        loaded_report = yaml.safe_load(report_file)

        for filename in loaded_report:
            if filename in report:
                for loaded_annotation in loaded_report[filename]:
                    found = False
                    for report_annotation in report[filename]:
                        index_keys = ('line_number', 'annotation_token', 'annotation_data')

                        if all([loaded_annotation[k] == report_annotation[k] for k in index_keys]):
                            report_annotation.update(loaded_annotation)
                            found = True
                            break

                    if not found:
                        report[filename].append(loaded_annotation)
            else:
                report[filename] = loaded_report[filename]

    def _aggregate_reports(self):
        """
        Combine all of the given report files into a single report object.
        """
        report = collections.defaultdict(list)

        # Combine report files into a single dict. If there are duplicate annotations, make sure we have the superset
        # of data.
        for r in self.report_files:
            self._add_report_file_to_full_report(r, report)

        return report

    def _write_doc_file(self, doc_filename, doc_data):
        """
        Write out a single report file with the given data. This is rendered using the configured top level template.

        Args:
            doc_filename: Filename to write to.
            doc_data: Dict of reporting data to use, in the {'file name': [list, of, annotations,]} style.
        """
        full_doc_filename = os.path.join(
            self.config.rendered_report_dir,
            slugify(doc_filename)
        )

        full_doc_filename += self.config.rendered_report_file_extension

        self.echo.echo_v(f'Writing {full_doc_filename}')

        with open(full_doc_filename, 'w') as output:
            output.write(self.top_level_template.render(
                create_time=self.create_time,
                report=doc_data,
                all_choices=self.all_choices,
                all_annotations=self.config.annotation_tokens,
                group_mapping=self.group_mapping,
                slugify=slugify,
                source_link_prefix=self.config.rendered_report_source_link_prefix)
            )

    def _generate_per_choice_docs(self):
        """
        Generate a page of documentation for each configured annotation choice.
        """
        for choice in self.all_choices:
            choice_report = collections.defaultdict(list)
            for filename in self.full_report:
                for annotation in self.full_report[filename]:
                    if isinstance(annotation['annotation_data'], list) and choice in annotation['annotation_data']:
                        choice_report[filename].append(annotation)

            self._write_doc_file(f'choice_{choice}', choice_report)

    def _generate_per_annotation_docs(self):
        """
        Generate a page of documentation for each configured annotation.
        """
        for annotation in self.config.annotation_tokens:
            annotation_report = collections.defaultdict(list)
            for filename in self.full_report:
                for report_annotation in self.full_report[filename]:
                    if report_annotation['annotation_token'] == annotation:
                        annotation_report[filename].append(report_annotation)

            self._write_doc_file(f'annotation_{annotation}', annotation_report)

    def render(self):
        """
        Perform the rendering of all documentation using the configured Jinja2 templates.
        """
        # Generate the top level list of all annotations
        self._write_doc_file('index', self.full_report)
        self._generate_per_choice_docs()
        self._generate_per_annotation_docs()
