use pyo3::prelude::*;
use pyo3::types::PyString;
use std::io::{BufRead, BufReader};
use std::fs::File;

use regex::Regex;

const PYVER_RE_STR: &str = r"(?i)^#\s+x-requires-python:\s+(?<version>.+)$";
const HEADER_RE_STR: &str = r"(?i)^#\s+script\s+dependencies:\s*$";

mod snakerun_ex {
    pyo3::import_exception!(snakerun.exceptions, MetadataError);
}

#[pyfunction]
pub fn parse_pep722(source_path: &PyString) -> PyResult<(Option<String>, Vec<String>)> {
    // Make case insensitive header regex
    let pyver_re: Regex = Regex::new(PYVER_RE_STR).unwrap();
    let header_re: Regex = Regex::new(HEADER_RE_STR).unwrap();

    let mut pyver: Option<String> = None;
    let mut dependencies: Vec<String> = vec![];

    let source_file = File::open(source_path.to_str().unwrap())?;

    let source_reader = BufReader::new(source_file);

    let mut in_spec = false;  // Bool to note if we are reading the dependency list

    for line in source_reader.lines() {
        let line = line?;

        if in_spec {
            if line.starts_with("#") {
                let mut dependency = line[1..].trim();
                if !dependency.is_empty() {
                    // Remove in-line comment if present
                    if let Some(split_dep) = dependency.split_once(" # ") {
                        dependency = split_dep.0.trim();
                    }
                    dependencies.push(String::from(dependency));
                }
            } else {
                in_spec = false;
            }
        } else {
            if pyver.is_some() && !dependencies.is_empty() {
                break;
            }
            if header_re.is_match(line.as_str()) {
                if dependencies.is_empty() {
                    in_spec = true;
                } else {
                    return Err(snakerun_ex::MetadataError::new_err(
                        "Script dependencies block defined multiple times in script."
                    ));
                }
            } else {
                if let Some(pyver_captures) = pyver_re.captures(line.as_str()) {
                    let ver = pyver_captures.name("version").unwrap();

                    // Only add python version from the first example of this string
                    match pyver {
                        Some(_) => {
                            return Err(snakerun_ex::MetadataError::new_err(
                                "x-requires-python block defined multiple times in script."
                            ));
                        }
                        None => {
                            let mut ver_str = ver.as_str();
                            if let Some(sp) = ver_str.split_once(" # ") {
                                ver_str = sp.0;
                            }
                            pyver = Some(String::from(ver_str));
                        }
                    }
                }
            }
        }
    }
    Ok((pyver, dependencies))
}