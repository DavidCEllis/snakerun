mod pep_722_parser;

use pyo3::prelude::*;
use pep_722_parser::{parse_pep722};


#[pymodule]
fn internals_rs(py: Python<'_>, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse_pep722, m)?)?;
    Ok(())
}
