mod pep722_parser;
mod cli_parser;
mod cache_manager;

use pyo3::prelude::*;
use pep722_parser::{parse_pep722};


#[pymodule]
#[pyo3(name = "_internals_rs")]
fn internals(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_pep722, m)?)?;
    Ok(())
}
