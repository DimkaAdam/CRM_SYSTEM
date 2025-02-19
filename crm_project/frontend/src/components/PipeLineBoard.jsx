import { useState, useEffect } from "react";
import { DndContext, closestCorners } from "@dnd-kit/core";
import { SortableContext, horizontalListSortingStrategy } from "@dnd-kit/sortable";
import Column from "./Column";

const stages = ["new", "send_email", "meeting", "account", "deal"];

export default function PipelineBoard() {
  const [pipeline, setPipeline] = useState(() => {
    return stages.reduce((acc, stage) => {
      acc[stage] = [];
      return acc;
    }, {});
  });

  useEffect(() => {
    fetch("/api/pipeline/")
      .then((res) => res.json())
      .then((data) => {
        console.log("✅ API Response:", data);

        const grouped = stages.reduce((acc, stage) => {
          acc[stage] = data.filter((item) => item.stage === stage);
          return acc;
        }, {});

        console.log("✅ Grouped Data:", grouped);
        setPipeline(grouped);
      })
      .catch((error) => console.error("❌ Ошибка загрузки данных:", error));
  }, []);

  return (
    <DndContext collisionDetection={closestCorners}>
      {/* ✅ Принудительно делаем горизонтальную разметку */}
      <div className="flex flex-row gap-4 p-4 overflow-x-auto w-full">
        {stages.map((stage) => (
          <SortableContext key={stage} items={pipeline[stage] || []} strategy={horizontalListSortingStrategy}>
            <Column id={stage} title={stage.replace("_", " ").toUpperCase()} items={pipeline[stage] || []} />
          </SortableContext>
        ))}
      </div>
    </DndContext>
  );
}
