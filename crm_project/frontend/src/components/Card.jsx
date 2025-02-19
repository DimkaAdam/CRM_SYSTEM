import React from "react";
import { useDraggable } from "@dnd-kit/core";

export default function Card({ item }) {
  // ✅ Гарантируем, что `useDraggable` вызывается всегда
  const { attributes, listeners, setNodeRef, transform } = useDraggable({
    id: item?.id || "unknown", // ✅ Предотвращаем ошибку, даже если `item.id` нет
  });

  if (!item || !item.id) {
    console.error("❌ Ошибка: `item` или `item.id` отсутствует!", item);
    return <div className="bg-red-200 p-2">Ошибка загрузки</div>; // ✅ Вместо `null`, показываем ошибку
  }

  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : undefined;

  return (
    <div ref={setNodeRef} {...listeners} {...attributes} style={style} className="bg-white p-3 rounded-lg shadow-md">
      {item.company_name}
    </div>
  );
}
