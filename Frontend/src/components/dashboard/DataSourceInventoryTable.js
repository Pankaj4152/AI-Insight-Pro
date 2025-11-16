import React from 'react';

function DataSourceInventoryTable({ inventory }) {
  return (
    <div className="data-source-inventory-table">
      <table>
        <thead>
          <tr>
            <th>Data Store Name</th>
            <th>Type</th>
            <th>Region</th>
            <th>Last Scanned</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {inventory.map(source => (
            <tr key={source.id}>
              <td>{source.name}</td>
              <td>{source.type}</td>
              <td>{source.region}</td>
              <td>{source.lastScanned}</td>
              <td>{source.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DataSourceInventoryTable;