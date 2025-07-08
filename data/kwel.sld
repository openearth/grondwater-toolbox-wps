<?xml version="1.0" encoding="UTF-8"?>
<sld:UserStyle xmlns="http://www.opengis.net/sld" xmlns:sld="http://www.opengis.net/sld" xmlns:gml="http://www.opengis.net/gml" xmlns:ogc="http://www.opengis.net/ogc">
  <sld:Name>AtlasStyler 1.9</sld:Name>
  <sld:Title/>
  <sld:FeatureTypeStyle>
    <sld:Name>RASTER_COLORMAP_INTERVALS:PALETTE#YlOrRd:NODATAVALUE#-999.0:METHOD#QUANTILES</sld:Name>
    <sld:Title>RasterRulesList_Intervals</sld:Title>
    <sld:FeatureTypeName>Feature</sld:FeatureTypeName>
    <sld:Rule>
      <sld:Name>NAMEColors for value-ranges</sld:Name>
      <sld:Title>TITLEColors for value-ranges</sld:Title>
      <ogc:Filter>
        <ogc:And>
          <ogc:PropertyIsEqualTo>
            <ogc:Literal>ALL_LABEL_CLASSES_ENABLED</ogc:Literal>
            <ogc:Literal>ALL_LABEL_CLASSES_ENABLED</ogc:Literal>
          </ogc:PropertyIsEqualTo>
          <ogc:PropertyIsEqualTo>
            <ogc:Literal>1</ogc:Literal>
            <ogc:Literal>1</ogc:Literal>
          </ogc:PropertyIsEqualTo>
        </ogc:And>
      </ogc:Filter>
      <sld:MaxScaleDenominator>1.7976931348623157E308</sld:MaxScaleDenominator>
      <sld:RasterSymbolizer>
        <sld:Geometry>
          <ogc:PropertyName>geom</ogc:PropertyName>
        </sld:Geometry>
        <sld:ChannelSelection>
          <sld:GrayChannel>
            <sld:SourceChannelName>1</sld:SourceChannelName>
          </sld:GrayChannel>
        </sld:ChannelSelection>
        <sld:ColorMap type="intervals">
          <sld:ColorMapEntry color="#990000" opacity="0.01" quantity="-20.000000" label="Inzijging (mm/dag)"/>
          <sld:ColorMapEntry color="#D60000" opacity="1.0" quantity="-2.000000" label="-2.00"/>
          <sld:ColorMapEntry color="#FF2626" opacity="1.0" quantity="-1.000000" label="-1.00"/>
          <sld:ColorMapEntry color="#FF9B9B" opacity="1.0" quantity="-0.5000000" label="-0.50"/>
          <sld:ColorMapEntry color="#FFDBDB" opacity="1.0" quantity="-0.2500000" label="-0.2500000"/>
          <sld:ColorMapEntry color="#D8D8D8" opacity="1.0" quantity="-0.1000000" label="-0.10"/>
          <sld:ColorMapEntry color="#DBDBFF" opacity="1.0" quantity="0.1000000" label="0.10"/>
          <sld:ColorMapEntry color="#9B9BFF" opacity="1.0" quantity="0.2500000" label="0.25"/>
          <sld:ColorMapEntry color="#2727FF" opacity="1.0" quantity="0.5000000" label="0.50"/>
          <sld:ColorMapEntry color="#0000D6" opacity="1.0" quantity="1.000000" label="1.00"/>
          <sld:ColorMapEntry color="#000099" opacity="1.0" quantity="2.000000" label="2.00"/>
          <sld:ColorMapEntry color="#000099" opacity="0.01" quantity="9.9999998E+30" label="Kwel mm/dag)"/>
         </sld:ColorMap>
      </sld:RasterSymbolizer>
    </sld:Rule>
  </sld:FeatureTypeStyle>
</sld:UserStyle>
