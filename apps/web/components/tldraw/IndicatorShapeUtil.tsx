"use client";

import { HTMLContainer, Rectangle2d, ShapeUtil, TLBaseShape } from "tldraw";

import { IndicatorShapeCard } from "./IndicatorShape";

export type IndicatorShape = TLBaseShape<
  "indicator",
  {
    w: number;
    h: number;
    indicatorKey: string;
    variant: "metric" | "theme" | "stock";
    seriesKey?: string;
  }
>;

export class IndicatorShapeUtil extends ShapeUtil<IndicatorShape> {
  static override type = "indicator" as const;

  override canEdit() {
    return false;
  }

  override canResize() {
    return true;
  }

  override getDefaultProps(): IndicatorShape["props"] {
    return {
      w: 360,
      h: 280,
      indicatorKey: "market_turnover",
      variant: "metric",
    };
  }

  override getGeometry(shape: IndicatorShape) {
    return new Rectangle2d({
      width: shape.props.w,
      height: shape.props.h,
      isFilled: true,
    });
  }

  override component(shape: IndicatorShape) {
    return (
      <HTMLContainer style={{ width: shape.props.w, height: shape.props.h }}>
        <IndicatorShapeCard shape={shape} />
      </HTMLContainer>
    );
  }

  override indicator() {
    return null;
  }
}
