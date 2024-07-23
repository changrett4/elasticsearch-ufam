import React from "react";

const ResultadosPesquisa = ({ results }) => {
    const rows = [];
    for (let i = 0; i < Math.min(results.length, 12); i += 1) {
        rows.push(results.slice(i, i + 1));
    }

    return (
        <table>
            <thead>
            </thead>
            <tbody>
                {rows.map((row, rowIndex) => (
                    <tr key={rowIndex}>
                        {row.map((result, colIndex) => (
                            <td key={colIndex}>
                                <div>
                                    
                                    <div>{result.title}</div>
                                    <img src={result.imgUrl} alt={result.title} />
                                    <div>{result.description}</div>
                                </div>
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
    );
};

export default ResultadosPesquisa;
